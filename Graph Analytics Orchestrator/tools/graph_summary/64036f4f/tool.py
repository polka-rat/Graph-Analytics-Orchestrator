from graphkit.contract import error, get_graph, ok


def run(store, graph_id, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(sorted(params))}. graph_summary takes only graph_id.")

    n = g.number_of_nodes()
    m = g.number_of_edges()
    possible_edges = n * (n - 1) if g.directed else n * (n - 1) / 2
    density = m / possible_edges if possible_edges else 0.0
    average_degree = (2 * m / n) if n else 0.0

    result = {
        "graph_id": g.graph_id,
        "directed": g.directed,
        "weighted": g.weighted,
        "node_count": n,
        "edge_count": m,
        "density": round(density, 6),
        "average_degree": round(average_degree, 6),
    }
    if g.directed:
        result["average_in_degree"] = round(m / n if n else 0.0, 6)
        result["average_out_degree"] = round(m / n if n else 0.0, 6)

    kind = "a directed" if g.directed else "an undirected"
    summary = (
        f"Graph '{graph_id}' is {kind} graph with {n} nodes and {m} edges; "
        f"its density is {result['density']} and average degree is {result['average_degree']}."
    )
    return ok(result, summary)
