"""Compare two nodes by their common neighbours and Jaccard similarity."""
from graphkit.contract import check_node, error, get_graph, node_ref, ok


def run(store, graph_id: str, node: str = None, other: str = None, **params) -> dict:
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. node_similarity takes graph_id, node, and other.")
    for value, name in ((node, "node"), (other, "other")):
        err = check_node(g, value, name)
        if err:
            return err
    if node == other:
        return error("node and other must be different nodes.")

    left = set(g.undirected_neighbors(node))
    right = set(g.undirected_neighbors(other))
    common = sorted(left & right)
    union = left | right
    score = round(len(common) / len(union), 6) if union else 0.0
    result = {
        "node": node_ref(g, node),
        "other": node_ref(g, other),
        "common_neighbors": [node_ref(g, n) for n in common],
        "common_count": len(common),
        "jaccard": score,
    }
    summary = (f"{result['node']['label']} and {result['other']['label']} have "
               f"{len(common)} common neighbours and Jaccard similarity {score}.")
    return ok(result, summary)

