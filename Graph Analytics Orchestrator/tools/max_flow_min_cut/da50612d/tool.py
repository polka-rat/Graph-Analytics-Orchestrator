"""Maximum flow between a source and a sink (Edmonds-Karp), with the minimum cut.

Edmonds-Karp repeatedly finds a shortest augmenting path (fewest edges) in the residual
network by breadth-first search and pushes the bottleneck capacity along it. When no path is
left, the nodes that can still reach the sink form the sink side of a minimum cut, and the edges
crossing into that side are the bottleneck. An undirected edge can carry flow either way, as in
networkx.maximum_flow.

Rules (the validator checks them):
- Implement the algorithm yourself: standard library, NumPy and graphkit only.
- Get graphs only from the store; never open files, print, or use the network.
- Never crash: return error("what went wrong and how to fix it") instead.
- Return every node as node_ref(g, node, ...), so it has both an id and a label.
- Keep the output under 8 KB: respect top_k.
- Be deterministic: same input, same output.
"""
import json
from collections import deque

from graphkit.contract import MAX_OUTPUT_BYTES, check_node, check_top_k, error, get_graph, node_ref, ok

# Leave room below the 8 KB limit for the summary and the JSON keys.
_SIZE_BUDGET = MAX_OUTPUT_BYTES - 600
_EPS = 1e-9


def _capacities(g, capacity):
    """[(u, v, capacity)] for every edge, or an error dict."""
    edges = list(g.edges())
    if capacity == "weight":
        caps = [(u, v, w) for u, v, w in edges]
    elif capacity == "unit":
        caps = [(u, v, 1.0) for u, v, _ in edges]
    else:
        caps = []
        for u, v, _ in edges:
            value = g.edge_attrs(u, v).get(capacity)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                names = sorted({"weight", "unit"} | (set(g.edge_attrs(*edges[0][:2])) if edges else set()))
                return None, error(f"Edge {u}->{v} of '{g.graph_id}' has no numeric attribute '{capacity}'. "
                                   f"Use capacity = one of: {', '.join(names)}.")
            caps.append((u, v, float(value)))
    bad = next(((u, v, c) for u, v, c in caps if c < 0), None)
    if bad:
        return None, error(f"Edge {bad[0]}->{bad[1]} has negative capacity {bad[2]}; flows need capacities >= 0. "
                           f"Use capacity='unit' to count edges instead.")
    return caps, None


def _edmonds_karp(nodes, caps, directed, source, sink):
    """Return (flow value, set of node indices on the source side of a minimum cut).

    Arcs are stored in flat lists; arc a and arc a ^ 1 are each other's reverse. A directed edge
    u->v gets a reverse arc of capacity 0; an undirected edge gets capacity c in both directions.
    """
    index = {n: i for i, n in enumerate(nodes)}
    head, residual = [], []
    adj = [[] for _ in nodes]
    for u, v, c in caps:
        i, j = index[u], index[v]
        if i == j:
            continue                      # a self-loop never helps a flow
        adj[i].append(len(head)); head.append(j); residual.append(c)
        adj[j].append(len(head)); head.append(i); residual.append(0.0 if directed else c)

    s, t = index[source], index[sink]
    total = 0.0
    while True:
        parent_arc = [-1] * len(nodes)
        parent_arc[s] = -2
        queue = deque([s])
        while queue and parent_arc[t] == -1:
            x = queue.popleft()
            for a in adj[x]:
                y = head[a]
                if parent_arc[y] == -1 and residual[a] > _EPS:
                    parent_arc[y] = a
                    if y == t:
                        break
                    queue.append(y)
        if parent_arc[t] == -1:
            break
        # Walk back from the sink to find the bottleneck, then push it along the path.
        path, y = [], t
        while y != s:
            a = parent_arc[y]
            path.append(a)
            y = head[a ^ 1]
        push = min(residual[a] for a in path)
        for a in path:
            residual[a] -= push
            residual[a ^ 1] += push
        total += push

    # Sink side of the minimum cut: the nodes that can still reach the sink in the residual
    # network (searched backwards from the sink). Everything else is the source side. This is the
    # same minimum cut that networkx.minimum_cut reports.
    sink_side = {t}
    queue = deque([t])
    while queue:
        y = queue.popleft()
        for a in adj[y]:
            x = head[a]                   # arc a ^ 1 runs x -> y
            if x not in sink_side and residual[a ^ 1] > _EPS:
                sink_side.add(x)
                queue.append(x)
    return total, set(range(len(nodes))) - sink_side


def _number(x):
    x = round(float(x), 6)
    return int(x) if x == int(x) else x


def _fit(out, items):
    """Drop entries from the end of `items` (a list inside `out`) until the output fits in 8 KB."""
    while items and len(json.dumps(out).encode("utf-8")) > _SIZE_BUDGET:
        items.pop()
    return len(items)


def run(store, graph_id, source=None, sink=None, capacity="weight", top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. max_flow_min_cut takes graph_id, source, "
                     f"sink, capacity and top_k.")
    if source is None or sink is None:
        return error("Give both 'source' and 'sink' as node ids (use lookup_node to find them).")
    for param, node in (("source", source), ("sink", sink)):
        err = check_node(g, node, param)
        if err:
            return err
    if source == sink:
        return error(f"source and sink are the same node ('{source}'); choose two different nodes.")
    if not isinstance(capacity, str) or not capacity:
        return error("capacity must be 'weight', 'unit' or the name of a numeric edge attribute.")
    k, err = check_top_k(top_k)
    if err:
        return err
    caps, err = _capacities(g, capacity)
    if err:
        return err

    nodes = g.nodes()
    value, side = _edmonds_karp(nodes, caps, g.directed, source, sink)
    in_source_side = {nodes[i] for i in side}

    cut = []
    for u, v, c in caps:
        if u in in_source_side and v not in in_source_side:
            cut.append((u, v, c))
        elif not g.directed and v in in_source_side and u not in in_source_side:
            cut.append((v, u, c))     # report undirected cut edges from the source side outwards
    cut.sort(key=lambda e: (-e[2], e[0], e[1]))
    shown_edges = [{"from": node_ref(g, u), "to": node_ref(g, v), "capacity": _number(c)} for u, v, c in cut[:k]]

    flow = _number(value)
    result = {
        "source": node_ref(g, source),
        "sink": node_ref(g, sink),
        "capacity": capacity,
        "max_flow_value": flow,
        "cut_size": len(cut),
        "cut_capacity": _number(sum(c for _, _, c in cut)),
        "source_side_size": len(in_source_side),
        "sink_side_size": len(nodes) - len(in_source_side),
        "cut_edges": shown_edges,
    }
    shown = _fit({"status": "ok", "result": result, "summary": "x" * 400, "result_graph_id": None, "error": None},
                 shown_edges)

    s_name, t_name = f"{g.label(source)} ({source})", f"{g.label(sink)} ({sink})"
    unit = {"weight": "weight" if g.weighted else "edge(s)", "unit": "edge(s)"}.get(capacity, capacity)
    if value <= _EPS:
        summary = (f"There is no path from {s_name} to {t_name} in '{graph_id}', so the maximum flow is 0 "
                   f"and no edge needs to be cut.")
    else:
        names = "; ".join(f"{e['from']['id']}->{e['to']['id']} ({e['capacity']})" for e in shown_edges[:3])
        summary = (f"The maximum flow from {s_name} to {t_name} is {flow} ({unit} as capacity). "
                   f"The minimum cut has {len(cut)} edge(s) with the same total capacity; the largest: {names}. "
                   f"Showing {shown} cut edge(s).")
    return ok(result, summary)
