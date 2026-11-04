"""Maximum flow (Edmonds-Karp) between two nodes, plus a minimum cut."""
import json
from collections import deque

from graphkit.contract import check_node, check_top_k, error, get_graph, node_ref, ok

EPS = 1e-9
MAX_BYTES = 7000  # keep well under the 8 KB output limit


def _capacities(g, capacity):
    """{u: {v: capacity}} of directed arcs (an undirected edge gives an arc each way), or an error dict."""
    cap = {n: {} for n in g.nodes()}
    for u, v, w in g.edges():
        if capacity == "weight":
            c = w
        elif capacity == "unit":
            c = 1.0
        else:
            c = g.edge_attrs(u, v).get(capacity)
            if isinstance(c, bool) or not isinstance(c, (int, float)):
                return None, error(f"Edges of '{g.graph_id}' have no numeric attribute {capacity!r} "
                                   f"(edge {u}->{v} has {c!r}). Use capacity='weight' or 'unit'.")
        if c < 0:
            return None, error(f"Edge {u}->{v} has negative capacity {c}; capacities must be non-negative.")
        cap[u][v] = cap[u].get(v, 0.0) + c
        if not g.directed:
            cap[v][u] = cap[v].get(u, 0.0) + c
    return cap, None


def _edmonds_karp(cap, source, sink):
    """Returns (flow value, residual capacities). BFS finds shortest augmenting paths."""
    res = {u: dict(nbrs) for u, nbrs in cap.items()}
    for u, nbrs in cap.items():
        for v in nbrs:
            res[v].setdefault(u, 0.0)
    total = 0.0
    while True:
        parent = {source: None}
        queue = deque([source])
        while queue and sink not in parent:
            u = queue.popleft()
            for v in sorted(res[u]):
                if v not in parent and res[u][v] > EPS:
                    parent[v] = u
                    queue.append(v)
        if sink not in parent:
            return total, res
        bottleneck, v = float("inf"), sink
        while parent[v] is not None:
            bottleneck = min(bottleneck, res[parent[v]][v])
            v = parent[v]
        v = sink
        while parent[v] is not None:
            u = parent[v]
            res[u][v] -= bottleneck
            res[v][u] += bottleneck
            v = u
        total += bottleneck


def run(store, graph_id, source=None, sink=None, capacity="weight", top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     f"max_flow_min_cut takes graph_id, source, sink, capacity and top_k.")
    k, err = check_top_k(top_k)
    if err:
        return err
    for value, name in ((source, "source"), (sink, "sink")):
        err = check_node(g, value, name)
        if err:
            return err
    if source == sink:
        return error("source and sink must be different nodes.")
    if not isinstance(capacity, str) or not capacity:
        return error("capacity must be 'weight', 'unit' or the name of a numeric edge attribute.")

    cap, err = _capacities(g, capacity)
    if err:
        return err
    flow, res = _edmonds_karp(cap, source, sink)

    # Source side of the minimum cut: nodes still reachable from the source in the residual graph.
    side, queue = {source}, deque([source])
    while queue:
        u = queue.popleft()
        for v, r in res[u].items():
            if v not in side and r > EPS:
                side.add(v)
                queue.append(v)
    cut = [(u, v, c) for u in side for v, c in cap[u].items() if v not in side and c > EPS]
    cut.sort(key=lambda e: (-e[2], e[0], e[1]))

    flow = round(flow, 6)
    name = {"weight": "edge weights", "unit": "unit capacities"}.get(capacity, f"'{capacity}' values")
    s, t = g.label(source), g.label(sink)
    result = {
        "max_flow": flow,
        "source": node_ref(g, source),
        "sink": node_ref(g, sink),
        "capacity": capacity,
        "cut_size": len(cut),
        "source_side_size": len(side),
        "sink_side_size": g.number_of_nodes() - len(side),
        "cut_edges": [{"from": node_ref(g, u), "to": node_ref(g, v), "capacity": round(c, 6)}
                      for u, v, c in cut[:k]],
    }
    while len(json.dumps(result)) > MAX_BYTES:
        result["cut_edges"].pop()
    if flow <= EPS:
        summary = f"No path from {s} ({source}) to {t} ({sink}), so the maximum flow is 0 and nothing needs cutting."
    else:
        summary = (f"Maximum flow from {s} ({source}) to {t} ({sink}) is {flow} using {name}. "
                   f"The minimum cut has {len(cut)} edge{'s' if len(cut) != 1 else ''} with total capacity {flow}.")
        if len(result["cut_edges"]) < len(cut):
            summary += f" Listing the {len(result['cut_edges'])} largest cut edges."
    return ok(result, summary)
