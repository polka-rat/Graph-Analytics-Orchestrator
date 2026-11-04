"""Rank graph nodes by their unweighted degree."""
import json

from graphkit.contract import check_top_k, error, get_graph, node_ref, ok
from graphkit.graph import Graph

MAX_OUTPUT_BYTES = 8 * 1024


def _fits(result, summary):
    response = ok(result, summary)
    return len(json.dumps(response, allow_nan=False, sort_keys=True).encode("utf-8")) <= MAX_OUTPUT_BYTES


def run(store, graph_id: str, top_k=10, **params) -> dict:
    try:
        g, err = get_graph(store, graph_id)
    except AttributeError:
        return error("store must provide get(graph_id). Pass the graph store supplied to the tool.")
    if err:
        return err
    if not isinstance(g, Graph):
        return error("The selected graph is not a supported Graph. Choose a graph returned by the graph store.")
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. Remove them; supported parameters are top_k.")
    k, err = check_top_k(top_k)
    if err:
        return err

    scored = []
    for node in g.nodes():
        if g.directed:
            in_degree = len(g.in_neighbors(node))
            out_degree = len(g.out_neighbors(node))
            degree = in_degree + out_degree
            scored.append((degree, node, in_degree, out_degree))
        else:
            degree = len(g.out_neighbors(node))
            scored.append((degree, node, None, None))
    scored.sort(key=lambda item: (-item[0], item[1]))

    result = []
    for degree, node, in_degree, out_degree in scored[:k]:
        extra = {"degree": degree}
        if g.directed:
            extra.update(in_degree=in_degree, out_degree=out_degree)
        candidate = result + [node_ref(g, node, **extra)]
        summary = (f"Returned {len(candidate)} of the top {min(k, len(scored))} nodes by degree "
                   f"in '{graph_id}'.")
        if not _fits(candidate, summary):
            break
        result = candidate

    if not result:
        if not scored:
            return ok([], f"Graph '{graph_id}' has no nodes to rank.")
        return error("Node metadata is too large to fit the 8 KB response limit. Use a graph with shorter node labels.")
    return ok(result, f"Returned {len(result)} of the top {min(k, len(scored))} nodes by degree in '{graph_id}'.")
