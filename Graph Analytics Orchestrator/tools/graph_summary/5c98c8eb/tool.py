"""Compute basic structural statistics for a graph.

Rules (the validator checks them):
- Implement the algorithm yourself: standard library, NumPy and graphkit only.
- Get graphs only from the store; never open files, print, or use the network.
- Never crash: return error("what went wrong and how to fix it") instead.
- Return every node as node_ref(g, node, ...), so it has both an id and a label.
- Keep the output under 8 KB: respect top_k.
- Be deterministic: same input, same output. Randomised algorithms take a `seed` parameter (default 0).
"""
from graphkit.contract import check_node, check_top_k, error, get_graph, node_ref, ok


def run(store, graph_id, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}.")

    # TODO: your algorithm. Useful Graph methods:
    #   g.nodes(), g.number_of_nodes(), g.number_of_edges(), g.directed, g.weighted
    #   g.out_neighbors(n), g.in_neighbors(n), g.undirected_neighbors(n)   -> {neighbour: weight}
    #   g.edges() -> (u, v, weight), g.weight(u, v), g.label(n), g.node_attrs(n)
    n = g.number_of_nodes()
    m = g.number_of_edges()

    if n <= 1:
        density = 0.0
    elif g.directed:
        density = m / (n * (n - 1))
    else:
        density = (2 * m) / (n * (n - 1))

    average_degree = (2 * m / n) if n else 0.0

    if g.directed:
        average_in_degree = m / n if n else 0.0
        average_out_degree = m / n if n else 0.0
    else:
        average_in_degree = None
        average_out_degree = None

    result = {
        "graph_id": graph_id,
        "directed": g.directed,
        "weighted": g.weighted,
        "number_of_nodes": n,
        "number_of_edges": m,
        "density": round(density, 6),
        "average_degree": round(average_degree, 6),
        "average_in_degree": (
            round(average_in_degree, 6)
            if average_in_degree is not None else None
        ),
        "average_out_degree": (
            round(average_out_degree, 6)
            if average_out_degree is not None else None
        ),
    }

    graph_type = "directed" if g.directed else "undirected"
    weight_type = "weighted" if g.weighted else "unweighted"

    summary = (
        f"Graph '{graph_id}' is {graph_type} and {weight_type}, with "
        f"{n} nodes, {m} edges, density {result['density']}, "
        f"and average degree {result['average_degree']}."
    )
    return ok(result, summary)

    # A tool that produces a node set or subgraph (marked with an arrow in the menu) registers it:
    #     sub_id = store.subgraph(graph_id, nodes, "Largest community of 'karate'")
    #     return ok(result, summary, result_graph_id=sub_id)
    # If it produces several node sets (e.g. communities), register each one, put its id in that
    # entry of the result as "graph_id", and return the largest one's id as result_graph_id.
