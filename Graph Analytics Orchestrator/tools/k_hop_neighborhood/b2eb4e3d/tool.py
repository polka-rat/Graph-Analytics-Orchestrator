"""k_hop_neighborhood: every node within k hops of a centre node, found by breadth-first search.

Rules (the validator checks them):
- Standard library, NumPy and graphkit only.
- Graphs come from the store only.
"""
import json

from graphkit.contract import (DEFAULT_TOP_K, MAX_OUTPUT_BYTES, check_node, check_top_k,
                               error, get_graph, node_ref, ok)

DIRECTIONS = ("out", "in", "both")


def _neighbors(g, node, direction):
    """Neighbours of `node` for the chosen direction (undirected graphs ignore it)."""
    if not g.directed or direction == "out":
        return g.out_neighbors(node)
    if direction == "in":
        return g.in_neighbors(node)
    return g.undirected_neighbors(node)


def _register(store, graph_id, nodes, description):
    """Register the subgraph once; an identical query reuses the same id (deterministic output)."""
    for meta in store.list_graphs():
        if meta["parent_id"] == graph_id and meta["description"] == description:
            return meta["graph_id"]
    return store.subgraph(graph_id, nodes, description)


def run(store, graph_id, node=None, k=1, direction="out", top_k=DEFAULT_TOP_K, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. k_hop_neighborhood takes "
                     "graph_id, node, k, direction and top_k.")

    defaulted = node is None
    if defaulted:
        if g.number_of_nodes() == 0:
            return error(f"Graph '{graph_id}' has no nodes.")
        # No centre given: use the best-connected node, ties broken by node id.
        node = min(g.nodes(), key=lambda n: (-len(g.undirected_neighbors(n)), n))
    else:
        err = check_node(g, node)
        if err:
            return err

    if isinstance(k, bool) or not isinstance(k, int) or k < 1:
        return error(f"k must be a whole number of at least 1; got {k!r}.")
    if direction not in DIRECTIONS:
        return error(f"direction must be one of {', '.join(DIRECTIONS)}; got {direction!r}.")
    top, err = check_top_k(top_k)
    if err:
        return err

    # Breadth-first search, one level per hop. First sighting of a node is its shortest distance.
    dist = {node: 0}
    frontier = [node]
    for hop in range(1, k + 1):
        next_frontier = []
        for u in frontier:
            for v in _neighbors(g, u, direction):
                if v not in dist:
                    dist[v] = hop
                    next_frontier.append(v)
        if not next_frontier:
            break
        frontier = next_frontier

    # Deterministic order: nearest first, ties broken by node id ascending.
    reached = sorted((n for n in dist if n != node), key=lambda n: (dist[n], n))

    count_by_distance = {}
    for n in reached:
        key = str(dist[n])
        count_by_distance[key] = count_by_distance.get(key, 0) + 1

    name = f"{g.label(node)} ({node})"
    scope = f" following {direction} edges" if g.directed else ""
    description = f"{k}-hop neighbourhood of {name} in {graph_id}{scope}"
    try:
        sub_id = _register(store, graph_id, [node] + reached, description)
    except ValueError as exc:
        return error(f"Could not register the neighbourhood subgraph: {exc}")

    result = {
        "center": node_ref(g, node),
        "default_center": defaulted,
        "k": k,
        "direction": direction if g.directed else "undirected",
        "total_reached": len(reached),
        "count_by_distance": count_by_distance,
        "nodes": [node_ref(g, n, distance=dist[n]) for n in reached[:top]],
        "truncated": False,
    }
    # Stay under the 8 KB output limit, leaving room for the summary.
    while result["nodes"] and len(json.dumps(result)) > MAX_OUTPUT_BYTES - 1024:
        result["nodes"].pop()
    result["truncated"] = len(result["nodes"]) < len(reached)

    note = (" No node was given, so the best-connected node was used as the centre."
            if defaulted else "")
    summary = (f"{len(reached)} nodes are within {k} hops of {name}{scope}; "
               f"{len(result['nodes'])} are listed, nearest first. "
               f"The full neighbourhood is registered as graph '{sub_id}'.{note}")
    return ok(result, summary, result_graph_id=sub_id)