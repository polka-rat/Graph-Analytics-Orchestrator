import json
from collections import deque
from fractions import Fraction

from graphkit.contract import MAX_OUTPUT_BYTES, check_top_k, error, get_graph, node_ref, ok

OUTPUT_BUDGET = MAX_OUTPUT_BYTES - 256
WORK_LIMIT = 60000000
MAX_SPLITS_SHOWN = 10


def _working_graph(g):
    nodes = g.nodes()
    adj = {}
    for n in nodes:
        adj[n] = {}
    for u in nodes:
        for v in g.out_neighbors(u):
            if u != v:
                adj[u][v] = None
                adj[v][u] = None
    edges = []
    seen = set()
    for u in nodes:
        for v in adj[u]:
            if v not in seen:
                adj[u][v] = len(edges)
                adj[v][u] = len(edges)
                edges.append((u, v))
        seen.add(u)
    return nodes, adj, edges


def _accumulate(adj, source, raw):
    order = []
    preds = {source: []}
    sigma = {source: 1.0}
    dist = {source: 0}
    queue = deque([source])
    work = 0
    while queue:
        v = queue.popleft()
        order.append(v)
        next_dist = dist[v] + 1
        sv = sigma[v]
        work += len(adj[v])
        for w, e in adj[v].items():
            d = dist.get(w)
            if d is None:
                queue.append(w)
                dist[w] = next_dist
                sigma[w] = sv
                preds[w] = [(v, e)]
            elif d == next_dist:
                sigma[w] += sv
                preds[w].append((v, e))
    delta = {}
    for w in order:
        delta[w] = 0
    for w in reversed(order):
        coeff = (1 + delta[w]) / sigma[w]
        for v, e in preds[w]:
            c = sigma[v] * coeff
            raw[e] += c
            delta[v] += c
    return work


def _reachable(adj, start):
    seen = {start}
    queue = deque([start])
    while queue:
        u = queue.popleft()
        for w in adj[u]:
            if w not in seen:
                seen.add(w)
                queue.append(w)
    return seen


def _modularity(edges, degree, label, m):
    inside = {}
    total = {}
    for u, v in edges:
        if label[u] == label[v]:
            inside[label[u]] = inside.get(label[u], 0) + 1
    for n, d in degree.items():
        total[label[n]] = total.get(label[n], 0) + d
    score = 0
    for c, t in total.items():
        score += 4 * m * inside.get(c, 0) - t * t
    return Fraction(score, 4 * m * m)


def _round(x, digits):
    value = round(float(x), digits)
    if value == 0:
        value = 0.0
    return value


def _size(out):
    return len(json.dumps(out, sort_keys=True).encode("utf-8"))


def run(store, graph_id, num_communities=None, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     f"girvan_newman takes graph_id, num_communities and top_k.")
    top_k, err = check_top_k(top_k)
    if err:
        return err

    nodes, adj, edges = _working_graph(g)
    n = len(nodes)
    m = len(edges)
    if num_communities is not None:
        if isinstance(num_communities, bool) or not isinstance(num_communities, int) or not 1 <= num_communities <= n:
            return error(f"num_communities must be a whole number from 1 to {n} (the number of nodes in "
                         f"'{graph_id}'), or left out to pick the split with the highest modularity; "
                         f"got {num_communities!r}.")
    if m == 0:
        return error(f"Graph '{graph_id}' has no edges (other than self-loops), so there is nothing for "
                     f"Girvan-Newman to remove: every node is already on its own.")
    if n * 2 * m * 10 > WORK_LIMIT:
        return error(f"Girvan-Newman is too slow for '{graph_id}' ({n} nodes, {m} undirected edges): it "
                     f"recomputes all shortest paths after every edge removal. Run it on a smaller subgraph "
                     f"(e.g. from k_hop_neighborhood or filter_nodes), or use louvain or label_propagation.")

    degree = {}
    for u in nodes:
        degree[u] = len(adj[u])
    scale = 1 / (n * (n - 1))
    raw = [0.0] * m
    alive = [True] * m
    work = 0
    for s in nodes:
        work += _accumulate(adj, s, raw)

    label = {}
    n_parts = 0
    for s in nodes:
        if s not in label:
            for x in _reachable(adj, s):
                label[x] = n_parts
            n_parts += 1
    level0 = (_modularity(edges, degree, label, m), 0, dict(label), n_parts)
    best = None
    splits = []
    removed = 0
    target = num_communities
    while removed < m and (target is None or n_parts < target):
        if work > WORK_LIMIT:
            if target is None:
                hint = "pass num_communities (stopping early is much faster), "
            elif target > 2:
                hint = "pass a smaller num_communities, "
            else:
                hint = ""
            return error(f"Girvan-Newman ran out of time on '{graph_id}' ({n} nodes, {m} edges) after removing "
                         f"{removed} edges. To get an answer, {hint}run it on a smaller subgraph "
                         f"(e.g. from k_hop_neighborhood or filter_nodes), or use louvain or label_propagation.")
        top = -1
        top_val = None
        for e in range(m):
            if alive[e]:
                val = raw[e] * scale
                if top_val is None or val > top_val:
                    top = e
                    top_val = val
        u, v = edges[top]
        del adj[u][v]
        del adj[v][u]
        alive[top] = False
        removed += 1

        part_u = _reachable(adj, u)
        if v in part_u:
            part_v = set()
        else:
            part_v = _reachable(adj, v)
        affected = part_u | part_v
        for x in affected:
            for e in adj[x].values():
                raw[e] = 0.0
        for s in nodes:
            if s in affected:
                work += _accumulate(adj, s, raw)

        if part_v:
            for x in part_v:
                label[x] = n_parts
            n_parts += 1
            q = _modularity(edges, degree, label, m)
            if len(splits) < MAX_SPLITS_SHOWN:
                sizes = sorted([len(part_u), len(part_v)], reverse=True)
                splits.append({"num_communities": n_parts, "edges_removed": removed, "modularity": _round(q, 6),
                               "split_sizes": sizes})
            if target is not None or best is None or q > best[0]:
                best = (q, removed, dict(label), n_parts)

    if best is None:
        best = level0
    q, removed_at, labels, n_comm = best
    return _report(store, g, graph_id, nodes, degree, labels, n_comm, q, removed_at, splits, target,
                   level0, top_k)


def _report(store, g, graph_id, nodes, degree, labels, n_comm, q, removed_at, splits, target, level0, top_k):
    groups = {}
    for x in nodes:
        if labels[x] not in groups:
            groups[labels[x]] = []
        groups[labels[x]].append(x)
    communities = sorted(groups.values(), key=lambda c: (-len(c), min(c)))
    for c in communities:
        c.sort(key=lambda x: (-degree[x], x))
    listed = communities[:top_k]
    sub_ids = []
    for i, c in enumerate(listed, 1):
        sub_ids.append(store.subgraph(graph_id, c, f"Girvan-Newman community {i} of {n_comm} in '{graph_id}' "
                                                   f"({len(c)} nodes)"))

    if g.directed and g.weighted:
        note = " Edge direction and weights are ignored."
    elif g.directed:
        note = " Edge direction is ignored."
    elif g.weighted:
        note = " Edge weights are ignored."
    else:
        note = ""
    q_text = f"{_round(q, 3):.3f}"
    if target is not None and removed_at == 0:
        how = (f"'{graph_id}' already falls into {n_comm} separate parts, which are returned as its "
               f"communities (no edge removed, modularity {q_text}).")
        chosen_by = "num_communities (already separate parts)"
    elif target is not None:
        how = (f"Girvan-Newman splits '{graph_id}' into {n_comm} communities, as asked, after removing the "
               f"{removed_at} most between edges (modularity {q_text}).")
        chosen_by = "num_communities"
    else:
        how = (f"Girvan-Newman splits '{graph_id}' into {n_comm} communities after removing the {removed_at} "
               f"most between edges; this level has the highest modularity ({q_text}).")
        chosen_by = "highest modularity"
        if q <= level0[0]:
            how += (f" Even so, no split beats leaving the graph as its {level0[3]} connected part(s) "
                    f"(modularity {_round(level0[0], 3):.3f}), so its community structure is weak.")

    cap = 0
    for c in listed:
        cap = max(cap, len(c))
    shown = len(listed)
    while True:
        community_list = []
        for i in range(shown):
            c = listed[i]
            members = []
            for x in c[:cap]:
                members.append(node_ref(g, x))
            community_list.append({"size": len(c), "graph_id": sub_ids[i], "members": members})
        result = {"num_communities": n_comm, "modularity": _round(q, 6), "edges_removed": removed_at,
                  "chosen_by": chosen_by, "communities": community_list, "splits": splits}
        first = listed[0]
        names = []
        for x in first[:3]:
            names.append(g.label(x))
        if shown < n_comm or cap < len(first):
            more = f" Listed: the {shown} largest communities, with up to {cap} best-connected members each."
        else:
            more = ""
        summary = (f"{how} The largest has {len(first)} nodes, including {', '.join(names)} "
                   f"(subgraph '{sub_ids[0]}').{more}{note}")
        out = ok(result, summary, result_graph_id=sub_ids[0])
        if _size(out) <= OUTPUT_BUDGET or (cap == 1 and shown == 1):
            return out
        if cap > 5:
            cap = max(5, cap * 3 // 4)
        elif shown > 1:
            shown -= 1
        else:
            cap -= 1
