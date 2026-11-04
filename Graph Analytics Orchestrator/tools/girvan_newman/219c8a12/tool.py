import json
import time
from collections import deque

from graphkit.contract import MAX_OUTPUT_BYTES, check_top_k, error, get_graph, node_ref, ok

TARGET_BYTES = min(7500, MAX_OUTPUT_BYTES)

MAX_REMOVALS_LIMIT = 100_000
MAX_SECONDS_LIMIT = 25.0
SAMPLE_SIZES = (10, 5, 3, 1)
MAX_SPLITS_LISTED = 25
WORK_BUDGET = 120_000_000


class _OutOfTime(Exception):
    pass


class _OutOfWork(Exception):
    pass


def _rebuild(n, adj):
    new = [dict() for _ in range(n)]
    for u in range(n):
        for v in adj[u]:
            if u != v and v not in new[u]:
                new[u][v] = None
                new[v][u] = None
    return new


def _undirected_adjacency(g, nodes, index):
    n = len(nodes)
    if g.directed:
        succ = [[index[v] for v in g.out_neighbors(u)] for u in nodes]
        return _rebuild(n, succ)
    adj = [dict() for _ in range(n)]
    for u, v, _ in g.edges():
        iu, iv = index[u], index[v]
        adj[iu][iv] = None
        adj[iv][iu] = None
    return _rebuild(n, _rebuild(n, adj))


def _component(adj, start):
    seen = {start}
    queue = deque([start])
    while queue:
        v = queue.popleft()
        for w in adj[v]:
            if w not in seen:
                seen.add(w)
                queue.append(w)
    return seen


def _edge_betweenness(adj, comp, deadline, budget):
    cost = len(comp) * (len(comp) + sum(len(adj[v]) for v in comp))
    if cost > budget[0]:
        raise _OutOfWork
    budget[0] -= cost
    eb = {}
    for s in sorted(comp):
        if time.perf_counter() > deadline:
            raise _OutOfTime
        stack, pred = [], {s: []}
        sigma, dist = {s: 1.0}, {s: 0}
        queue = deque([s])
        while queue:
            v = queue.popleft()
            stack.append(v)
            dv, sv = dist[v], sigma[v]
            for w in adj[v]:
                if w not in dist:
                    queue.append(w)
                    dist[w] = dv + 1
                    sigma[w] = 0.0
                    pred[w] = []
                if dist[w] == dv + 1:
                    sigma[w] += sv
                    pred[w].append(v)
        delta = dict.fromkeys(stack, 0)
        while stack:
            w = stack.pop()
            coeff = (1 + delta[w]) / sigma[w]
            for v in pred[w]:
                c = sigma[v] * coeff
                key = (v, w) if v < w else (w, v)
                eb[key] = eb.get(key, 0.0) + c
                delta[v] += c
    return eb


def _modularity(labels, mod_edges, strength, total):
    inside, degree = {}, {}
    for (u, v), w in mod_edges.items():
        if labels[u] == labels[v]:
            inside[labels[u]] = inside.get(labels[u], 0.0) + w
    for i, s in enumerate(strength):
        degree[labels[i]] = degree.get(labels[i], 0.0) + s
    return sum(inside.get(c, 0.0) / total - (d / (2 * total)) ** 2 for c, d in degree.items())


def _labels(n, adj):
    labels = [-1] * n
    count = 0
    for i in range(n):
        if labels[i] < 0:
            for v in _component(adj, i):
                labels[v] = count
            count += 1
    return labels, count


def _size(out):
    return len(json.dumps(out, allow_nan=False, sort_keys=True).encode("utf-8"))


def run(store, graph_id, num_communities=None, max_removals=1000, top_k=10, community_index=0,
        weighted=True, max_seconds=20.0, **params):
    started = time.perf_counter()
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. girvan_newman takes graph_id, num_communities, "
                     f"max_removals, top_k, community_index, weighted and max_seconds.")
    k, err = check_top_k(top_k)
    if err:
        return err
    n = g.number_of_nodes()
    if num_communities is not None and (isinstance(num_communities, bool) or not isinstance(num_communities, int)
                                        or not 1 <= num_communities <= max(n, 1)):
        return error(f"num_communities must be a whole number from 1 to {n} (the number of nodes in "
                     f"'{graph_id}'), or omitted to get the split with the highest modularity; got {num_communities!r}.")
    if isinstance(max_removals, bool) or not isinstance(max_removals, int) or not 1 <= max_removals <= MAX_REMOVALS_LIMIT:
        return error(f"max_removals must be a whole number from 1 to {MAX_REMOVALS_LIMIT}; got {max_removals!r}.")
    if isinstance(community_index, bool) or not isinstance(community_index, int) or community_index < 0:
        return error(f"community_index must be a whole number of at least 0 (0 = largest community); "
                     f"got {community_index!r}.")
    if not isinstance(weighted, bool):
        return error("weighted must be true or false.")
    if isinstance(max_seconds, bool) or not isinstance(max_seconds, (int, float)) or not 0 < max_seconds <= MAX_SECONDS_LIMIT:
        return error(f"max_seconds must be a number above 0 and at most {MAX_SECONDS_LIMIT:g}; got {max_seconds!r}.")

    nodes = g.nodes()
    index = {v: i for i, v in enumerate(nodes)}
    adj = _undirected_adjacency(g, nodes, index)
    n_edges = sum(len(a) for a in adj) // 2
    if n_edges == 0:
        return error(f"Graph '{graph_id}' has no edges (self-loops do not count), so there is nothing to split "
                     f"into communities. Use list_graphs to pick a graph with edges.")

    rank = {}
    for u in range(n):
        for pos, v in enumerate(adj[u]):
            if v > u:
                rank[(u, v)] = (u, pos)
    edge_order = sorted(rank, key=rank.__getitem__)

    use_weights = weighted and g.weighted
    mod_edges = {}
    strength = [0.0] * n
    for u in range(n):
        for v in adj[u]:
            if u < v:
                w = g.undirected_neighbors(nodes[u])[nodes[v]] if use_weights else 1.0
                mod_edges[(u, v)] = w
                strength[u] += w
                strength[v] += w
    total = sum(mod_edges.values())
    if total <= 0:
        return error(f"The edge weights of '{graph_id}' sum to zero, so modularity is undefined; "
                     f"run girvan_newman with weighted=false.")

    labels, count = _labels(n, adj)
    start_count = count
    levels = [(count, _modularity(labels, mod_edges, strength, total), 0, labels[:])]
    deadline = started + max_seconds
    budget = [WORK_BUDGET]
    scale = 1.0 / (n * (n - 1)) if n > 1 else 1.0
    removed = 0
    stop_reason = None
    target_reached = num_communities is not None and count >= num_communities

    if not target_reached:
        eb = {}
        try:
            for c in range(count):
                eb.update(_edge_betweenness(adj, [i for i in range(n) if labels[i] == c], deadline, budget))
            while eb:
                if removed >= max_removals:
                    stop_reason = "max_removals"
                    break
                best_key, best_val = None, None
                for key in edge_order:
                    if key in eb:
                        val = eb[key] * scale
                        if best_val is None or val > best_val:
                            best_key, best_val = key, val
                u, v = best_key
                del adj[u][v], adj[v][u]
                removed += 1
                comp_u = _component(adj, u)
                comp_v = comp_u if v in comp_u else _component(adj, v)
                old = comp_u | comp_v
                for key in [e for e in eb if e[0] in old]:
                    del eb[key]
                eb.update(_edge_betweenness(adj, comp_u, deadline, budget))
                if comp_v is not comp_u:
                    eb.update(_edge_betweenness(adj, comp_v, deadline, budget))
                    count += 1
                    for x in comp_v:
                        labels[x] = count - 1
                    levels.append((count, _modularity(labels, mod_edges, strength, total), removed, labels[:]))
                    if num_communities is not None and count >= num_communities:
                        target_reached = True
                        break
        except _OutOfTime:
            stop_reason = "time"
        except _OutOfWork:
            stop_reason = "work"

    if num_communities is not None:
        chosen = levels[-1]
    else:
        chosen = levels[0]
        for lv in levels[1:]:
            if lv[1] > chosen[1] + 1e-12:
                chosen = lv
    n_comm, q, at_removal, lab = chosen

    groups = {}
    for i, c in enumerate(lab):
        groups.setdefault(c, []).append(i)
    degree = [len(g.undirected_neighbors(v)) for v in nodes]
    communities = sorted(groups.values(), key=lambda m: (-len(m), min(nodes[i] for i in m)))
    communities = [sorted(m, key=lambda i: (-degree[i], nodes[i])) for m in communities]
    if community_index >= n_comm:
        return error(f"community_index must be from 0 to {n_comm - 1}: the chosen split has {n_comm} communities.")

    root_desc = f"found by Girvan-Newman on '{graph_id}'"
    shown_ids = {}
    for ci in sorted(set(range(min(k, n_comm))) | {community_index}):
        shown_ids[ci] = store.subgraph(graph_id, [nodes[i] for i in communities[ci]],
                                       f"Community {ci} of {n_comm} ({len(communities[ci])} nodes) {root_desc}")
    result_graph_id = shown_ids[community_index]

    def communities_text(c):
        return f"{c} communit{'y' if c == 1 else 'ies'}"

    why = {"time": f"the {max_seconds:g}-second time budget ran out",
           "work": "its fixed work limit was reached (it keeps the run well inside the time limit)",
           "max_removals": f"the max_removals={max_removals} limit was reached"}.get(stop_reason, "no edges were left")
    largest = f"the largest has {len(communities[0])} of {n} nodes"
    no_split = bool(stop_reason) and len(levels) == 1
    if no_split:
        if stop_reason == "max_removals":
            lead = (f"Girvan-Newman found no split of '{graph_id}': {why}, so all {n} nodes stay in one community.")
        else:
            lead = (f"Girvan-Newman found no split of '{graph_id}' because it is too slow for a graph with {n_edges} "
                    f"edges: it stopped after {removed} edge removals to stay within the time limit, so all {n} nodes "
                    f"stay in one community.")
    elif num_communities is not None and start_count > num_communities:
        lead = (f"'{graph_id}' already has {start_count} separate components, more than the {num_communities} "
                f"requested, so Girvan-Newman removed no edges (modularity {round(q, 6)}); {largest}.")
    elif num_communities is not None and not target_reached:
        lead = (f"Girvan-Newman split '{graph_id}' into {communities_text(n_comm)}, not the {num_communities} "
                f"requested, because {why} (modularity {round(q, 6)}, {at_removal} edges removed); {largest}.")
    elif num_communities is not None:
        lead = (f"Girvan-Newman splits '{graph_id}' into the requested {communities_text(n_comm)} by removing "
                f"{at_removal} edges (modularity {round(q, 6)}); {largest}.")
    else:
        best = (f"the best of {len(levels)} splits found before {why}" if stop_reason
                else f"the highest of the {len(levels)} splits explored")
        lead = (f"Girvan-Newman splits '{graph_id}' into {communities_text(n_comm)} by removing {at_removal} edges "
                f"(modularity {round(q, 6)}, {best}); {largest}.")

    caveats = [f"community {community_index} is registered as subgraph '{result_graph_id}' (result_graph_id)"]
    if no_split and stop_reason == "max_removals":
        caveats.append("raise max_removals to keep going")
    elif no_split:
        caveats.append("narrow the graph first (e.g. with filter_nodes) or use a faster community-detection tool")
    if g.directed:
        caveats.append("edge direction was ignored")
    if g.weighted:
        caveats.append("edge removal ignores weights" + (" but modularity uses them" if use_weights
                                                          else " and so does modularity (weighted=false)"))

    def summary(extra):
        second = "; ".join(caveats + extra) + "."
        return f"{lead} {second[0].upper()}{second[1:]}"

    splits = [{"communities": lv[0], "modularity": round(lv[1], 6), "edges_removed": lv[2]} for lv in levels]
    chosen_pos = levels.index(chosen)
    max_splits = min(k, MAX_SPLITS_LISTED)
    listed_splits = splits[:max_splits]
    if chosen_pos >= max_splits:
        listed_splits = splits[:max_splits - 1] + [splits[chosen_pos]]
    for sample in [size for size in SAMPLE_SIZES if size <= k]:
        for listed in sorted({min(k, n_comm), min(k, n_comm, 20), min(k, n_comm, 10), min(k, n_comm, 5), 1},
                             reverse=True):
            entries = []
            for ci in range(listed):
                m = communities[ci]
                entries.append({"community": ci, "size": len(m), "graph_id": shown_ids[ci],
                                "sample_nodes": [node_ref(g, nodes[i]) for i in m[:sample]]})
            result = {"num_communities": n_comm, "modularity": round(q, 6), "edges_removed": at_removal,
                      "communities": entries, "splits": listed_splits}
            trimmed = []
            if listed < min(k, n_comm):
                trimmed.append(f"only the {listed} largest communities are listed to keep the response small")
            if len(splits) > max_splits:
                first = len(listed_splits) - (chosen_pos >= max_splits)
                if first == 0:
                    trimmed.append(f"'splits' shows only the chosen one of {len(splits)} splits")
                else:
                    trimmed.append(f"'splits' shows the first {first} of {len(splits)} splits"
                                   f"{' plus the chosen one' if chosen_pos >= max_splits else ''}")
            out = ok(result, summary(trimmed), result_graph_id=result_graph_id)
            if _size(out) <= TARGET_BYTES:
                return out
    result["splits"] = [splits[chosen_pos]]
    return ok(result, summary(["only the largest community and the chosen split are listed to keep the response small"]),
              result_graph_id=result_graph_id)
