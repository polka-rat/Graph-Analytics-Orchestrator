"""Part A, Task 2: node_degree tool.

Calculates the degree (number of connections) of a given node in a graph.
Follow the tool contract in bootcamp/README.md.
"""
from graphkit.contract import check_node, error, get_graph, node_ref, ok


def run(store, graph_id: str, node: str = None, **params) -> dict:
    g, err = get_graph(store, graph_id)
    if err:
        return err

    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. node_degree takes graph_id and node.")

    err = check_node(g, node)
    if err:
        return err

    if g.directed:
        out_degree = len(g.out_neighbors(node))
        in_degree = len(g.in_neighbors(node))
        degree = out_degree + in_degree
        result = node_ref(
            g,
            node,
            out_degree=out_degree,
            in_degree=in_degree,
            degree=degree,
        )
        summary = (
            f"{g.label(node)} ({node}) has "
            f"{out_degree} outgoing and {in_degree} incoming edges."
        )
    else:
        degree = len(g.neighbors(node))
        result = node_ref(g, node, degree=degree)
        summary = f"{g.label(node)} ({node}) has {degree} connections."

    return ok(result, summary)
