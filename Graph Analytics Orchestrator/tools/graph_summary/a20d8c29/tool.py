"""graph_summary: size, density and degree statistics for a whole graph.

Rules (the validator checks them):
- Implement the algorithm yourself: standard library, NumPy and graphkit only.
- Get graphs only from the store; never open files, print, or use the network.
- Never crash: return error("what went wrong and how to fix it") instead.
- Return every node as node_ref(g, node, ...), so it has both an id and a label.
- Keep the output under 8 KB.
- Be deterministic: same input, same output.
"""
from graphkit.contract import error, get_graph, node_ref, ok


def run(store, graph_id, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(
            f"Unknown parameter(s): {', '.join(sorted(params))}. "
            f"graph_summary takes only graph_id; it describes the whole graph, so it has no top_k."
        )

    n = g.number_of_nodes()
    m = g.number_of_edges()

    if n == 0:
        empty = {
            "graph_id": g.graph_id,
            "directed": g.directed,
            "weighted": g.weighted,
            "nodes": 0,
            "edges": 0,
            "density": 0.0,
            "average_degree": 0.0,
            "min_degree": 0,
            "max_degree": 0,
            "isolated_nodes": 0,
            "self_loops": 0,
            "most_connected": None,
        }
        return ok(empty, f"Graph '{g.graph_id}' is empty: it has no nodes and no edges.")

    # Degrees. For an undirected graph out_neighbors, in_neighbors and neighbors are
    # the same mapping, so the total degree of a node is simply its neighbour count.
    nodes = g.nodes()
    out_degree = {v: len(g.out_neighbors(v)) for v in nodes}
    if g.directed:
        in_degree = {v: len(g.in_neighbors(v)) for v in nodes}
        total_degree = {v: out_degree[v] + in_degree[v] for v in nodes}
    else:
        in_degree = out_degree
        total_degree = out_degree

    self_loops = sum(1 for v in nodes if v in g.out_neighbors(v))

    # Density = edges present / edges possible. A directed pair (u, v) has two possible
    # slots and an undirected pair only one, hence the factor of 2. Undefined for n < 2,
    # where it is reported as 0.0 (the same convention as networkx.density).
    if n < 2:
        density = 0.0
    elif g.directed:
        density = m / (n * (n - 1))
    else:
        density = 2 * m / (n * (n - 1))

    # Every edge contributes one out-stub and one in-stub, so the total degree sums to 2m
    # on directed and undirected graphs alike.
    average_degree = 2 * m / n

    degrees = list(total_degree.values())
    # Busiest node, ties broken by node id ascending so the output is deterministic.
    busiest = min(nodes, key=lambda v: (-total_degree[v], v))

    result = {
        "graph_id": g.graph_id,
        "directed": g.directed,
        "weighted": g.weighted,
        "nodes": n,
        "edges": m,
        "density": round(density, 6),
        "average_degree": round(average_degree, 6),
        "min_degree": min(degrees),
        "max_degree": max(degrees),
        "isolated_nodes": sum(1 for d in degrees if d == 0),
        "self_loops": self_loops,
        "most_connected": node_ref(g, busiest, degree=total_degree[busiest]),
    }

    if g.directed:
        # Each edge has exactly one tail and one head, so these two averages are equal.
        result["average_out_degree"] = round(m / n, 6)
        result["average_in_degree"] = round(m / n, 6)
        result["max_out_degree"] = max(out_degree.values())
        result["max_in_degree"] = max(in_degree.values())

    if g.weighted:
        weights = [w for _, _, w in g.edges()]
        result["total_edge_weight"] = round(sum(weights), 6) if weights else 0.0
        result["average_edge_weight"] = round(sum(weights) / len(weights), 6) if weights else 0.0
        result["min_edge_weight"] = round(min(weights), 6) if weights else 0.0
        result["max_edge_weight"] = round(max(weights), 6) if weights else 0.0

    kind = "directed" if g.directed else "undirected"
    weighting = "weighted" if g.weighted else "unweighted"
    summary = (
        f"Graph '{g.graph_id}' is {kind} and {weighting}, with {n:,} nodes and {m:,} edges "
        f"(density {result['density']}, average degree {result['average_degree']}). "
        f"The most connected node is {result['most_connected']['label']} "
        f"with {total_degree[busiest]} connections."
    )
    return ok(result, summary)
