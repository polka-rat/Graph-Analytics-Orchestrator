"""max_flow_min_cut: Edmonds-Karp maximum flow and the corresponding minimum cut.

Edge weights are capacities (unweighted graphs: every capacity is 1). On an undirected graph each
edge can carry flow in either direction up to its capacity.
"""
import json
from collections import deque

from graphkit.contract import check_node, check_top_k, error, get_graph, node_ref, ok

EPS = 1e-9
MAX_RESULT_BYTES = 6500  # the whole response must stay under 8 KB


def _build_residual(g, index):
    """Residual network as parallel arrays. Edge i and i^1 are a forward/backward pair."""
    to, cap, adj = [], [], [[] for _ in index]
    for u, v, w in g.edges():
        if u == v or w <= 0:
            continue
        iu, iv = index[u], index[v]
        adj[iu].append(len(to))
        to.append(iv)
        cap.append(float(w))
        adj[iv].append(len(to))
        to.append(iu)
        cap.append(float(w) if not g.directed else 0.0)  # undirected: usable both ways
    return to, cap, adj


def _bfs_augmenting_path(s, t, to, cap, adj):
    """Shortest augmenting path (fewest edges). Returns the edge used to reach each node, or None."""
    via = {s: -1}
    queue = deque([s])
    while queue:
        u = queue.popleft()
        for e in adj[u]:
            v = to[e]
            if v not in via and cap[e] > EPS:
                via[v] = e
                if v == t:
                    return via
                queue.append(v)
    return None


def run(store, graph_id, source=None, sink=None, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. This tool takes graph_id, source, sink and top_k.")
    if source is None or sink is None:
        return error("Give both 'source' and 'sink' node ids. Use lookup_node to find ids from names.")
    for value, name in ((source, "source"), (sink, "sink")):
        err = check_node(g, value, name)
        if err:
            return err
    k, err = check_top_k(top_k)
    if err:
        return err
    if source == sink:
        return error("'source' and 'sink' must be different nodes: the flow from a node to itself is not defined.")

    nodes = sorted(g.nodes())
    index = {n: i for i, n in enumerate(nodes)}
    to, cap, adj = _build_residual(g, index)
    s, t = index[source], index[sink]

    # ---- Edmonds-Karp: repeatedly push flow along a shortest augmenting path
    flow = 0.0
    while True:
        via = _bfs_augmenting_path(s, t, to, cap, adj)
        if via is None:
            break
        bottleneck, v = float("inf"), t
        while v != s:
            e = via[v]
            bottleneck = min(bottleneck, cap[e])
            v = to[e ^ 1]
        v = t
        while v != s:
            e = via[v]
            cap[e] -= bottleneck
            cap[e ^ 1] += bottleneck
            v = to[e ^ 1]
        flow += bottleneck

    # ---- min cut: nodes still reachable from the source in the residual network
    reach = {s}
    queue = deque([s])
    while queue:
        u = queue.popleft()
        for e in adj[u]:
            if to[e] not in reach and cap[e] > EPS:
                reach.add(to[e])
                queue.append(to[e])
    source_side = {nodes[i] for i in reach}

    cut = []
    for u, v, w in g.edges():
        if u == v or w <= 0:
            continue
        if g.directed:
            if u in source_side and v not in source_side:
                cut.append((u, v, w))
        elif (u in source_side) != (v in source_side):
            a, b = (u, v) if u in source_side else (v, u)  # orient from source side to sink side
            cut.append((a, b, w))
    cut.sort(key=lambda x: (-x[2], x[0], x[1]))
    cut_capacity = round(sum(w for _, _, w in cut), 6)
    flow = round(flow, 6)

    s_ref, t_ref = node_ref(g, source), node_ref(g, sink)
    if flow <= EPS:
        return error(f"No path exists from {s_ref['label']} ({source}) to {t_ref['label']} ({sink}), so no "
                     f"flow is possible. Check both ids with lookup_node, or try swapping source and sink "
                     f"(edges are directed in this graph)." if g.directed else
                     f"No path exists from {s_ref['label']} ({source}) to {t_ref['label']} ({sink}), so no "
                     f"flow is possible. They are in different parts of the graph; check both ids with lookup_node.")

    shown = [{"from": node_ref(g, a), "to": node_ref(g, b), "capacity": round(w, 6)} for a, b, w in cut[:k]]
    result = {"max_flow": flow, "source": s_ref, "sink": t_ref, "cut_capacity": cut_capacity,
              "cut_edges_total": len(cut), "cut_edges_returned": len(shown),
              "source_side_size": len(source_side), "sink_side_size": len(nodes) - len(source_side),
              "cut_edges": shown, "cut_edges_note": "Cut edges are listed largest capacity first."}
    while shown and len(json.dumps(result)) > MAX_RESULT_BYTES:
        shown = shown[:-1]
        result["cut_edges"], result["cut_edges_returned"] = shown, len(shown)

    unit = "" if g.weighted else " (every edge has capacity 1)"
    summary = (f"The maximum flow from {s_ref['label']} ({source}) to {t_ref['label']} ({sink}) is {flow}{unit}. "
               f"The minimum cut has {len(cut)} edge{'s' if len(cut) != 1 else ''} with total capacity "
               f"{cut_capacity}; {len(source_side)} nodes lie on the source side.")
    return ok(result, summary)
