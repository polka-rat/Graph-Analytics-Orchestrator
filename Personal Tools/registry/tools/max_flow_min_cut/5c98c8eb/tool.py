"""Compute maximum flow and a corresponding minimum cut using Edmonds-Karp."""

from collections import deque
from graphkit.contract import error, get_graph, node_ref, ok, check_top_k


def run(store, graph_id, source=None, sink=None, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err

    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}.")

    k, err = check_top_k(top_k)
    if err:
        return err

    if source is None or sink is None:
        return error("Provide both source and sink node IDs.")

    if not g.directed:
        return error("Maximum flow requires a directed graph.")

    nodes = list(g.nodes())
    node_set = set(nodes)

    if source not in node_set:
        return error(f"Unknown source node: {source}.")

    if sink not in node_set:
        return error(f"Unknown sink node: {sink}.")

    if source == sink:
        return error("Source and sink must be different nodes.")

    residual = {u: {} for u in nodes}
    original = {}

    for u, v, weight in g.edges():
        capacity = float(weight) if g.weighted else 1.0
        if capacity < 0:
            return error("Edge capacities must be non-negative.")

        residual[u][v] = residual[u].get(v, 0.0) + capacity
        residual[v].setdefault(u, 0.0)
        original[(u, v)] = original.get((u, v), 0.0) + capacity

    max_flow = 0.0

    while True:
        parent = {source: None}
        queue = deque([source])

        while queue and sink not in parent:
            u = queue.popleft()
            for v in sorted(residual[u], key=str):
                if v not in parent and residual[u][v] > 1e-12:
                    parent[v] = u
                    queue.append(v)
                    if v == sink:
                        break

        if sink not in parent:
            break

        amount = float("inf")
        v = sink
        while v != source:
            u = parent[v]
            amount = min(amount, residual[u][v])
            v = u

        v = sink
        while v != source:
            u = parent[v]
            residual[u][v] -= amount
            residual[v][u] = residual[v].get(u, 0.0) + amount
            v = u

        max_flow += amount

    reachable = {source}
    queue = deque([source])

    while queue:
        u = queue.popleft()
        for v in residual[u]:
            if v not in reachable and residual[u][v] > 1e-12:
                reachable.add(v)
                queue.append(v)

    other_side = node_set - reachable
    cut_edges = []

    for (u, v), capacity in original.items():
        if u in reachable and v in other_side:
            cut_edges.append({
                "source": node_ref(g, u),
                "target": node_ref(g, v),
                "capacity": round(capacity, 6),
            })

    cut_edges.sort(
        key=lambda e: (
            str(e["source"]["id"]),
            str(e["target"]["id"]),
        )
    )

    cut_capacity = round(sum(e["capacity"] for e in cut_edges), 6)

    result = {
        "graph_id": graph_id,
        "source": node_ref(g, source),
        "sink": node_ref(g, sink),
        "max_flow": round(max_flow, 6),
        "min_cut_capacity": cut_capacity,
        "source_side": [node_ref(g, n) for n in sorted(reachable, key=str)[:k]],
        "source_side_truncated": len(reachable) > k,
        "sink_side": [node_ref(g, n) for n in sorted(other_side, key=str)[:k]],
        "sink_side_truncated": len(other_side) > k,
        "cut_edges": cut_edges[:k],
        "cut_edges_truncated": len(cut_edges) > k,
    }

    summary = (
        f"Maximum flow from {g.label(source)} to {g.label(sink)} is "
        f"{round(max_flow, 6)}; minimum cut capacity is {cut_capacity}."
    )
    return ok(result, summary)
