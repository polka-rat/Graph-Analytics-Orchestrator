"""TODO: one line saying what this tool computes.

Rules (the validator checks them):
- Implement the algorithm yourself: standard library, NumPy and graphkit only.
- Get graphs only from the store; never open files, print, or use the network.
- Never crash: return error("what went wrong and how to fix it") instead.
- Return every node as node_ref(g, node, ...), so it has both an id and a label.
- Keep the output under 8 KB: respect top_k.
- Be deterministic: same input, same output. Randomised algorithms take a `seed` parameter (default 0).
"""
import json
from collections import deque

from graphkit.contract import MAX_OUTPUT_BYTES, check_node, error, get_graph, node_ref, ok

EPS = 1e-9
SIZE_BUDGET = MAX_OUTPUT_BYTES - 1200


def _edge_capacities(g, capacity):
    edges = []
    for u, v, w in g.edges():
        if capacity == "weight":
            c = w
        elif capacity == "unit":
            c = 1.0
        else:
            c = g.edge_attrs(u, v).get(capacity)
            if isinstance(c, bool) or not isinstance(c, (int, float)):
                return None, (f"Edge {u}->{v} has no numeric attribute '{capacity}'. Use capacity='weight', "
                              f"'unit', or a numeric edge attribute of '{g.graph_id}' (see list_graphs).")
        if c < 0:
            return None, f"Edge {u}->{v} has a negative capacity ({c}); capacities must be zero or more."
        edges.append((u, v, float(c)))
    return edges, None


def _residual(g, edges):
    res = {n: {} for n in g.nodes()}
    for u, v, c in edges:
        if u == v:
            continue
        arcs = [(u, v)] if g.directed else [(u, v), (v, u)]
        for a, b in arcs:
            res[a][b] = res[a].get(b, 0.0) + c
            res[b].setdefault(a, 0.0)
    return res


def _bfs(res, source, sink):
    parent = {source: None}
    queue = deque([source])
    while queue and sink not in parent:
        u = queue.popleft()
        for v, r in res[u].items():
            if r > EPS and v not in parent:
                parent[v] = u
                queue.append(v)
    return parent

# Max flow using Edmond Karp algorithm which finds bottleneck edge after a bfs
def _edmonds_karp(res, source, sink):
    flow = 0.0
    paths = 0
    while True:
        parent = _bfs(res, source, sink)
        if sink not in parent:
            return flow, paths
        bottleneck = float("inf")
        v = sink
        while parent[v] is not None:
            u = parent[v]
            bottleneck = min(bottleneck, res[u][v])
            v = u
        v = sink
        while parent[v] is not None:
            u = parent[v]
            res[u][v] -= bottleneck
            res[v][u] += bottleneck
            v = u
        flow += bottleneck
        paths += 1


def _can_reach_sink(res, sink):
    seen = {sink}
    queue = deque([sink])
    while queue:
        w = queue.popleft()
        for v in res[w]:
            if v not in seen and res[v][w] > EPS:
                seen.add(v)
                queue.append(v)
    return seen


def _size(obj):
    return len(json.dumps(obj).encode("utf-8"))


def run(store, graph_id, source=None, sink=None, capacity="weight", **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. max_flow_min_cut takes graph_id, source, sink "
                     f"and capacity.")
    for value, name in ((source, "source"), (sink, "sink")):
        err = check_node(g, value, name)
        if err:
            return err
    if source == sink:
        return error(f"source and sink are both '{source}'; give two different nodes.")
    if not isinstance(capacity, str) or not capacity:
        return error("capacity must be 'weight', 'unit', or the name of a numeric edge attribute such as 'airlines'.")

    edges, err = _edge_capacities(g, capacity)
    if err:
        return error(err)
    res = _residual(g, edges)
    flow, paths = _edmonds_karp(res, source, sink)
    source_side = set(g.nodes()) - _can_reach_sink(res, sink)

    cut = []
    for u, v, c in edges:
        if u in source_side and v not in source_side:
            cut.append((u, v, c))
        elif not g.directed and v in source_side and u not in source_side:
            cut.append((v, u, c))
    cut = [e for e in cut if e[2] > 0]
    cut.sort(key=lambda e: (-e[2], e[0], e[1]))

    result = {"source": node_ref(g, source),
              "sink": node_ref(g, sink),
              "capacity": capacity,
              "max_flow": round(flow, 6),
              "cut_capacity": round(sum(c for _, _, c in cut), 6),
              "num_cut_edges": len(cut),
              "source_side_size": len(source_side),
              "sink_side_size": g.number_of_nodes() - len(source_side),
              "augmenting_paths": paths,
              "cut_edges": [{"from": node_ref(g, u), "to": node_ref(g, v), "capacity": round(c, 6)}
                            for u, v, c in cut]}

    # Shrink output size to limit within size budget
    while _size(result) > SIZE_BUDGET and result["cut_edges"]:
        result["cut_edges"].pop()
    result["cut_edges_shown"] = len(result["cut_edges"])

    src, dst = f"{g.label(source)} ({source})", f"{g.label(sink)} ({sink})"
    if flow <= EPS:
        summary = (f"There is no path from {src} to {dst} in '{graph_id}', so the maximum flow is 0 and no edges "
                   f"need to be cut.")
        return ok(result, summary)
    arrow = "->" if g.directed else "--"
    top = "; ".join(f"{u} {arrow} {v} ({round(c, 6)})" for u, v, c in cut[:5])
    summary = (f"Maximum flow from {src} to {dst} is {round(flow, 6)} using capacity '{capacity}'. "
               f"The minimum cut (the bottleneck) has {len(cut)} edge(s) with total capacity {round(flow, 6)}, "
               f"splitting the graph into a source side of {len(source_side)} node(s) and a sink side of "
               f"{result['sink_side_size']} node(s); largest cut edges: {top}.")
    if result["cut_edges_shown"] < len(cut):
        summary += f" Only the {result['cut_edges_shown']} largest cut edges are listed to keep the output small."

    return ok(result, summary)

    # A tool that produces a node set or subgraph (marked with an arrow in the menu) registers it:
    #     sub_id = store.subgraph(graph_id, nodes, "Largest community of 'karate'")
    #     return ok(result, summary, result_graph_id=sub_id)
    # If it produces several node sets (e.g. communities), register each one, put its id in that
    # entry of the result as "graph_id", and return the largest one's id as result_graph_id.
