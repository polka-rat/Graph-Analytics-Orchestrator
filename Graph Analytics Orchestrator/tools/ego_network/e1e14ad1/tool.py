"""ego_network: the subgraph made of a node, its neighbours and every edge among them.

Registers the subgraph with the store (it keeps all edges between the members, neighbour-neighbour
ones included) and returns its size plus a short list of the neighbours.
"""
import json

from graphkit.contract import check_node, check_top_k, error, get_graph, node_ref, ok

DIRECTIONS = ("both", "out", "in")
SIZE_BUDGET = 7000  # bytes of JSON; the contract limit is 8 KB


def run(store, graph_id, node=None, direction="both", top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. ego_network takes graph_id, node, "
                     f"direction and top_k.")
    err = check_node(g, node)
    if err:
        return err
    if direction not in DIRECTIONS:
        return error(f"direction must be one of {', '.join(DIRECTIONS)}; got {direction!r}.")
    k, err = check_top_k(top_k)
    if err:
        return err

    # Neighbours: for directed graphs 'direction' picks who counts (undirected graphs ignore it).
    neighbors = set()
    if not g.directed or direction in ("both", "out"):
        neighbors |= set(g.out_neighbors(node))
    if not g.directed or direction in ("both", "in"):
        neighbors |= set(g.in_neighbors(node))
    neighbors.discard(node)  # ignore a self-loop

    ego = node_ref(g, node)
    description = f"Ego network of {ego['label']} ({node}) in '{graph_id}'"
    sub_id = store.subgraph(graph_id, [node, *sorted(neighbors)], description)
    sub = store.get(sub_id)
    result = {"ego": ego, "neighbors": len(neighbors), "nodes": sub.number_of_nodes(),
              "edges": sub.number_of_edges(), "neighbor_sample": [node_ref(g, n) for n in sorted(neighbors)[:k]]}
    while result["neighbor_sample"] and len(json.dumps(result)) + 600 > SIZE_BUDGET:
        result["neighbor_sample"].pop()  # long labels: list fewer neighbours rather than break the 8 KB cap

    d, shown = len(neighbors), len(result["neighbor_sample"])
    more = f" Listing {shown} of them." if d > shown else ""
    summary = (f"{ego['label']} ({node}) has {d} neighbour{'' if d == 1 else 's'}. Its ego network has "
               f"{result['nodes']} nodes and {result['edges']} edges.{more} Registered as subgraph '{sub_id}'.")
    return ok(result, summary, result_graph_id=sub_id)
