from graphkit.contract import error, get_graph, ok


def run(store, graph_id, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. graph_summary takes only graph_id.")

    n = g.number_of_nodes()
    m = g.number_of_edges()

    if n <= 1:
        density = 0.0
    elif g.directed:
        density = m / (n * (n - 1))
    else:
        density = 2 * m / (n * (n - 1))

    avg_degree = 2 * m / n if n else 0.0
    isolated = sum(1 for v in g.nodes() if not g.out_neighbors(v) and not g.in_neighbors(v))

    result = {
        "graph_id": graph_id,
        "directed": g.directed,
        "weighted": g.weighted,
        "nodes": n,
        "edges": m,
        "density": round(density, 6),
        "avg_degree": round(avg_degree, 6),
        "isolated_nodes": isolated,
    }
    if g.directed:
        result["avg_out_degree"] = result["avg_in_degree"] = round(m / n if n else 0.0, 6)

    kind = ("directed" if g.directed else "undirected") + (", weighted" if g.weighted else ", unweighted")
    if n == 0:
        summary = f"Graph '{graph_id}' ({kind}) has no nodes and no edges."
    else:
        summary = (f"Graph '{graph_id}' ({kind}) has {n} nodes and {m} edges; density is {result['density']} "
                   f"and the average degree is {result['avg_degree']}.")
        if g.directed:
            summary += (f" On average a node has {result['avg_out_degree']} outgoing edges "
                        f"and the same number of incoming edges.")
        if n == 1:
            summary += " With a single node no edge between distinct nodes is possible, so density is 0."
    return ok(result, summary)
