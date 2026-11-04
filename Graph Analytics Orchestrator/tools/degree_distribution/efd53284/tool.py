"""Degree distribution of a graph.

Counts how many nodes have each degree. On a directed graph the degree is
out_degree + in_degree, matching NetworkX's G.degree(). The result is a list
of {"degree": d, "count": n} buckets sorted by degree ascending.
"""
from graphkit.contract import error, get_graph, ok


def run(store, graph_id, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(
            f"Unknown parameter(s): {', '.join(params)}. "
            "degree_distribution takes only graph_id."
        )

    counts = {}
    nodes = g.nodes()
    for node in nodes:
        degree = len(g.out_neighbors(node))
        if g.directed:
            degree += len(g.in_neighbors(node))
        elif node in g.out_neighbors(node):
            # An undirected self-loop counts twice, as in NetworkX.
            degree += 1
        counts[degree] = counts.get(degree, 0) + 1

    if not nodes:
        return error(f"Graph '{graph_id}' has no nodes, so it has no degree distribution.")

    result = [
        {"degree": degree, "count": count}
        for degree, count in sorted(counts.items())
    ]
    degrees = [bucket["degree"] for bucket in result]
    mode = min(result, key=lambda bucket: (-bucket["count"], bucket["degree"]))
    kind = "total (out + in) degrees" if g.directed else "degrees"
    summary = (
        f"{g.number_of_nodes()} nodes in '{graph_id}' have {kind} from "
        f"{min(degrees)} to {max(degrees)}; the most common is degree "
        f"{mode['degree']} with {mode['count']} nodes."
    )
    return ok(result, summary)
