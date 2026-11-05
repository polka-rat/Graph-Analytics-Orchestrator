"""Girvan-Newman communities: repeatedly remove the edge with the highest betweenness."""
import json
import time
from collections import deque

from graphkit.contract import MAX_OUTPUT_BYTES, check_top_k, error, get_graph, node_ref, ok

WORK_LIMIT = 1.5e8    # n * m^2; above this a full run is too slow
TIME_BUDGET = 20.0    # seconds
SAMPLE_SIZES = (10, 5, 3, 1, 0)


def _add(adj, u, v):
    if u != v:  # girvan_newman drops self-loops
        adj[u].setdefault(v, None)
        adj[v].setdefault(u, None)


def _rebuild(nodes, adj):
    new = {u: {} for u in nodes}
    for u in nodes:
        for v in adj[u]:
            _add(new, u, v)
    return new


def build_adjacency(g):
    """Neighbour dicts in the order networkx's girvan_newman uses, so ties break the same way."""
    nodes = g.nodes()
    if g.directed:
        succ = {u: {} for u in nodes}
        for u, v, _ in g.edges():
            succ[u][v] = None
        return _rebuild(nodes, succ)
    adj = {u: {} for u in nodes}
    for u, v, _ in g.edges():
        _add(adj, u, v)
    return _rebuild(nodes, _rebuild(nodes, adj))


def edge_betweenness(nodes, adj):
    """Normalised edge betweenness (Brandes)."""
    bc = {}
    done = set()
    for u in nodes:
        for v in adj[u]:
            if v not in done:
                bc[(u, v)] = 0.0
        done.add(u)

    for s in nodes:
        order, preds = [], {s: []}
        sigma, dist = {s: 1.0}, {s: 0}
        queue = deque([s])
        while queue:
            v = queue.popleft()
            order.append(v)
            for w in adj[v]:
                if w not in dist:
                    queue.append(w)
                    dist[w] = dist[v] + 1
                    sigma[w], preds[w] = 0.0, []
                if dist[w] == dist[v] + 1:
                    sigma[w] += sigma[v]
                    preds[w].append(v)
        delta = dict.fromkeys(order, 0)
        while order:
            w = order.pop()
            coeff = (1 + delta[w]) / sigma[w]
            for v in preds[w]:
                c = sigma[v] * coeff
                if (v, w) in bc:
                    bc[(v, w)] += c
                else:
                    bc[(w, v)] += c
                delta[v] += c

    n = len(nodes)
    if n >= 2:
        scale = 1 / (n * (n - 1))
        for e in bc:
            bc[e] *= scale
    return bc


def components(nodes, adj):
    seen, comps = set(), []
    for start in nodes:
        if start in seen:
            continue
        seen.add(start)
        queue, comp = deque([start]), [start]
        while queue:
            u = queue.popleft()
            for v in adj[u]:
                if v not in seen:
                    seen.add(v)
                    comp.append(v)
                    queue.append(v)
        comps.append(comp)
    return comps


def connected(adj, a, b):
    seen, queue = {a}, deque([a])
    while queue:
        u = queue.popleft()
        if u == b:
            return True
        for v in adj[u]:
            if v not in seen:
                seen.add(v)
                queue.append(v)
    return False


def girvan_newman(nodes, adj, stop_at=None, deadline=None):
    """Yield (partition, removed edges) at the start and after every split."""
    partition = components(nodes, adj)
    removed = []
    yield partition, list(removed)
    edges_left = sum(len(nbrs) for nbrs in adj.values()) // 2
    while edges_left and (stop_at is None or len(partition) < stop_at):
        while True:
            if deadline is not None and time.perf_counter() > deadline:
                raise TimeoutError
            bc = edge_betweenness(nodes, adj)
            u, v = max(bc, key=bc.get)
            del adj[u][v]
            del adj[v][u]
            edges_left -= 1
            removed.append((u, v))
            if not connected(adj, u, v):
                break
        partition = components(nodes, adj)
        yield partition, list(removed)


def modularity(g, partition):
    """Modularity of a partition (undirected, weighted)."""
    community = {u: i for i, comp in enumerate(partition) for u in comp}
    inside = [0.0] * len(partition)
    degree = [0.0] * len(partition)
    total = 0.0
    for u in g.nodes():
        for v, w in g.undirected_neighbors(u).items():
            if u == v:
                continue
            degree[community[u]] += w
            total += w
            if community[u] == community[v]:
                inside[community[u]] += w / 2
    if total == 0:
        return None
    m = total / 2
    return sum(inside[i] / m - (degree[i] / total) ** 2 for i in range(len(partition)))


def too_big(graph_id, n, m, reason):
    return error(f"'{graph_id}' is too large for Girvan-Newman ({n} nodes, {m} edges): {reason} "
                 f"Use louvain or label_propagation for the whole graph, or run girvan_newman on a "
                 f"smaller subgraph (for example one made by filter_nodes or k_hop_neighborhood).")


def run(store, graph_id, num_communities=None, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     f"girvan_newman takes graph_id, num_communities and top_k.")
    k, err = check_top_k(top_k)
    if err:
        return err
    nodes = g.nodes()
    n = len(nodes)
    if num_communities is not None:
        if isinstance(num_communities, bool) or not isinstance(num_communities, int) or num_communities < 1:
            return error(f"num_communities must be a whole number of at least 1; got {num_communities!r}. "
                         f"Leave it out to get the split with the highest modularity.")
        if num_communities > n:
            return error(f"num_communities is {num_communities}, but '{graph_id}' has only {n} nodes.")
    if n == 0:
        return ok({"community_count": 0, "modularity": None, "communities": []},
                  f"Graph '{graph_id}' has no nodes, so it has no communities.")

    adj = build_adjacency(g)
    m = sum(len(nbrs) for nbrs in adj.values()) // 2
    if n * m * m > WORK_LIMIT:
        return too_big(graph_id, n, m, "it recomputes every shortest path after each edge removal, "
                                       "so it would not finish in the time limit.")
    levels = []
    try:
        for partition, removed in girvan_newman(nodes, adj, stop_at=num_communities,
                                                deadline=time.perf_counter() + TIME_BUDGET):
            levels.append((partition, removed, modularity(g, partition)))
    except TimeoutError:
        return too_big(graph_id, n, m, f"it did not finish within {TIME_BUDGET:.0f} seconds.")

    start = len(levels[0][0])
    if num_communities is not None:
        if num_communities < start:
            return error(f"'{graph_id}' already falls into {start} separate components, so it cannot be "
                         f"split into fewer; ask for at least {start} communities.")
        chosen = len(levels) - 1  # every split adds exactly one community
    else:
        scored = [i for i, level in enumerate(levels) if level[2] is not None]
        chosen = max(scored, key=lambda i: (levels[i][2], -i)) if scored else 0

    partition, removed, q = levels[chosen]
    groups = sorted((sorted(c) for c in partition), key=lambda c: (-len(c), c[0]))
    shown = groups[:k]
    sub_ids = [store.subgraph(graph_id, members, f"Girvan-Newman community {rank} of '{graph_id}'")
               for rank, members in enumerate(shown, 1)]

    def build(sample, count):
        entries = [{"rank": rank, "size": len(members), "graph_id": sub_ids[rank - 1],
                    "members": [node_ref(g, u) for u in members[:sample]],
                    "more_members": max(0, len(members) - sample)}
                   for rank, members in enumerate(shown[:count], 1)]
        result = {"community_count": len(groups),
                  "modularity": None if q is None else round(q, 6),
                  "communities": entries}
        return ok(result, summarize(g, graph_id, groups, removed, q, count), result_graph_id=sub_ids[0])

    def fits(out):
        return len(json.dumps(out, sort_keys=True).encode("utf-8")) <= MAX_OUTPUT_BYTES

    for sample in SAMPLE_SIZES:
        out = build(sample, len(shown))
        if fits(out):
            return out
    count = len(shown)
    while count > 1 and not fits(out):
        count -= 1
        out = build(0, count)
    return out


def summarize(g, graph_id, groups, removed, q, shown):
    if q is None:
        who = f"each of its {len(groups)} nodes is" if len(groups) > 1 else "its only node is"
        text = f"'{graph_id}' has no edges, so Girvan-Newman has nothing to remove: {who} its own community."
    else:
        largest = groups[0]
        names = ", ".join(g.label(u) for u in largest[:3])
        text = (f"Girvan-Newman splits '{graph_id}' into {len(groups)} communities after removing "
                f"{len(removed)} edges (modularity {q:.3f}). The largest has {len(largest)} "
                f"nodes, including {names}.")
        if shown < len(groups):
            text += f" The {shown} largest are listed."
    if g.directed:
        text += " Edge direction was ignored."
    return text
