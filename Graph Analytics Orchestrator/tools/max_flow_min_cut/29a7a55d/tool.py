"""max_flow_min_cut: Edmonds–Karp maximum flow, with the cut edges.

Edge weights are capacities. The tool repeatedly finds a shortest augmenting
path from source to sink with BFS (Edmonds–Karp), pushes the path's bottleneck
through the residual network, and stops when the sink is no longer reachable.
The minimum cut is then read off the residual network, as in NetworkX: the
source side is every node that can no longer reach the sink; the cut edges are
the original edges leading out of that side. By the max-flow min-cut theorem
their total capacity equals the maximum flow.

Rules (the validator checks them):
- Implement the algorithm yourself: standard library, NumPy and graphkit only.
- Get graphs only from the store; never open files, print, or use the network.
- Never crash: return error("what went wrong and how to fix it") instead.
- Return every node as node_ref(g, node, ...), so it has both an id and a label.
- Keep the output under 8 KB: cut edges and the source side honour top_k.
- Be deterministic: same input, same output (BFS explores neighbours in a fixed order).
"""
from collections import deque

from graphkit.contract import check_node, check_top_k, error, get_graph, node_ref, ok

SOURCE_SIDE_SAMPLE = 10  # how many source-side nodes to list at most (count is exact)


def _residual(g):
    """res[u][v] = remaining capacity. An undirected edge is a pair of directed
    edges with the same capacity, like NetworkX builds them."""
    res = {u: {} for u in g.nodes()}
    for u, v, w in g.edges():
        res[u][v] = res[u].get(v, 0.0) + w
        if not g.directed:
            res[v][u] = res[v].get(u, 0.0) + w
    return res


def _shortest_augmenting_path(res, source, sink):
    """BFS in the residual network; returns the path as a node list or None."""
    parent = {source: None}
    queue = deque([source])
    while queue:
        u = queue.popleft()
        for v, cap in res[u].items():
            if cap > 0.0 and v not in parent:
                parent[v] = u
                if v == sink:
                    path = [sink]
                    while parent[path[-1]] is not None:
                        path.append(parent[path[-1]])
                    return path[::-1]
                queue.append(v)
    return None


def _edmonds_karp(res, source, sink):
    """Push flow along shortest augmenting paths until the sink is cut off."""
    pushed = 0.0
    while True:
        path = _shortest_augmenting_path(res, source, sink)
        if path is None:
            return pushed
        bottleneck = min(res[u][v] for u, v in zip(path, path[1:]))
        for u, v in zip(path, path[1:]):
            res[u][v] -= bottleneck
            res[v][u] = res[v].get(u, 0.0) + bottleneck
        pushed += bottleneck


def _source_side(res, sink):
    """Nodes on the source side of the minimum cut: those that can no longer
    reach the sink in the residual network. (NetworkX defines the minimum-cut
    partition the same way, by reverse search from the sink over edges with
    spare capacity; it is the same partition for every maximum flow.)"""
    incoming = {v: {} for v in res}
    for u, nbrs in res.items():
        for v, cap in nbrs.items():
            incoming[v][u] = cap
    reaches_sink = {sink}
    queue = deque([sink])
    while queue:
        v = queue.popleft()
        for u, cap in incoming[v].items():
            if cap > 0.0 and u not in reaches_sink:
                reaches_sink.add(u)
                queue.append(u)
    return set(res) - reaches_sink


def run(store, graph_id, source=None, sink=None, top_k=10, **params) -> dict:
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     "max_flow_min_cut takes graph_id, source, sink and top_k.")
    err = check_node(g, source, "source")
    if err:
        return err
    err = check_node(g, sink, "sink")
    if err:
        return err
    if source == sink:
        return error(f"source and sink are both '{source}'. "
                     "Choose two different nodes to compute a flow between.")
    k, err = check_top_k(top_k)
    if err:
        return err

    res = _residual(g)
    _edmonds_karp(res, source, sink)
    side = _source_side(res, sink)

    # The minimum cut: original edges from the reachable side to the rest.
    cut_edges = []
    for u, v, w in g.edges():
        if u in side and v not in side:
            cut_edges.append((u, v, w))
        elif not g.directed and v in side and u not in side:
            cut_edges.append((v, u, w))  # list an undirected edge from the source side

    flow_value = sum(w for _, _, w in cut_edges)
    cut_edges.sort(key=lambda e: (e[0], e[1]))
    result = {
        "source": node_ref(g, source),
        "sink": node_ref(g, sink),
        "flow_value": round(flow_value, 6),
        "min_cut": {
            "cut_edges_count": len(cut_edges),
            "cut_edges": [{"source": u, "target": v, "capacity": round(w, 6)}
                          for u, v, w in cut_edges[:k]],
            "source_side_count": len(side),
            "source_side": [node_ref(g, n) for n in sorted(side)[:SOURCE_SIDE_SAMPLE]],
        },
    }
    if cut_edges:
        summary = (f"Maximum flow from {g.label(source)} to {g.label(sink)} is "
                   f"{round(flow_value, 6)}; the minimum cut has {len(cut_edges)} edge(s) "
                   f"with total capacity {round(flow_value, 6)}, and "
                   f"{len(side)} node(s) stay on the source side.")
    else:
        summary = (f"{g.label(source)} cannot reach {g.label(sink)}, "
                   f"so the maximum flow is 0.")
    return ok(result, summary)
