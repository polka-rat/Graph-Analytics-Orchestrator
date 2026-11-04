"""node_similarity: common neighbours and Jaccard score of two nodes.

The Jaccard score of two nodes is |neighbours(a) ∩ neighbours(b)| divided by
|neighbours(a) ∪ neighbours(b)|: 1.0 means the two nodes connect to exactly the
same others, 0.0 means they share nobody. On directed graphs direction is ignored
(neighbours = everyone connected in either direction).

Rules (the validator checks them):
- Implement the algorithm yourself: standard library, NumPy and graphkit only.
- Get graphs only from the store; never open files, print, or use the network.
- Never crash: return error("what went wrong and how to fix it") instead.
- Return every node as node_ref(g, node, ...), so it has both an id and a label.
- Keep the output under 8 KB: cap the number of listed neighbours.
- Be deterministic: same input, same output.
"""
from graphkit.contract import check_node, error, get_graph, node_ref, ok

MAX_LISTED = 20  # how many common neighbours to list (the count is always exact)


def run(store, graph_id, node_a=None, node_b=None, **params) -> dict:
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     "node_similarity takes graph_id, node_a and node_b.")
    err = check_node(g, node_a, "node_a")
    if err:
        return err
    err = check_node(g, node_b, "node_b")
    if err:
        return err
    if node_a == node_b:
        return error(f"node_a and node_b are both '{node_a}'. "
                     "Choose two different nodes to compare.")

    neighbours_a = set(g.undirected_neighbors(node_a))
    neighbours_b = set(g.undirected_neighbors(node_b))
    common = sorted(neighbours_a & neighbours_b)
    union_size = len(neighbours_a | neighbours_b)
    jaccard = len(common) / union_size if union_size else 0.0

    result = {
        "node_a": node_ref(g, node_a, degree=len(neighbours_a)),
        "node_b": node_ref(g, node_b, degree=len(neighbours_b)),
        "common_neighbors_count": len(common),
        "common_neighbors": [node_ref(g, n) for n in common[:MAX_LISTED]],
        "union_size": union_size,
        "jaccard": round(jaccard, 6),
    }
    label_a, label_b = g.label(node_a), g.label(node_b)
    if common:
        summary = (f"{label_a} and {label_b} share {len(common)} neighbour(s) "
                   f"(Jaccard {round(jaccard, 6)} over a union of {union_size} nodes).")
    else:
        summary = (f"{label_a} and {label_b} share no neighbours (Jaccard 0.0); "
                   f"their neighbourhoods together span {union_size} nodes.")
    return ok(result, summary)
