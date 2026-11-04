"""ego_network: the subgraph formed by one node and the nodes around it.

Author: b2d75536. Easy tier, subgraph category.

The ego network of a node ("the ego") is the ego together with every node it can
reach in `radius` steps ("the alters"), plus all edges among those nodes. It is
found with a breadth-first search and the induced subgraph is registered in the
store, so another tool can run on it.
"""
import json

from graphkit.contract import MAX_OUTPUT_BYTES, check_node, check_top_k, error, get_graph, node_ref, ok

DIRECTIONS = ("both", "out", "in")
MAX_RADIUS = 5


def _neighbors(g, node, direction):
    """Neighbours of `node` in the direction asked for; undirected graphs ignore direction."""
    if not g.directed or direction == "both":
        return g.undirected_neighbors(node)
    return g.out_neighbors(node) if direction == "out" else g.in_neighbors(node)


def _reachable(g, center, radius, direction):
    """Breadth-first search from `center`, at most `radius` steps. Keeps discovery order."""
    seen = {center: 0}
    frontier = [center]
    for step in range(1, radius + 1):
        nxt = []
        for node in frontier:
            for neighbour in _neighbors(g, node, direction):
                if neighbour not in seen:
                    seen[neighbour] = step
                    nxt.append(neighbour)
        if not nxt:
            break
        frontier = nxt
    return seen


def _density(sub):
    """Fraction of the possible edges that are present."""
    n, e = sub.number_of_nodes(), sub.number_of_edges()
    if n < 2:
        return 0.0
    possible = n * (n - 1) if sub.directed else n * (n - 1) / 2
    return e / possible


def _fits(result, summary, result_graph_id):
    """True if this output stays inside the 8 KB the contract allows."""
    text = json.dumps(ok(result, summary, result_graph_id), allow_nan=False, sort_keys=True)
    return len(text.encode("utf-8")) <= MAX_OUTPUT_BYTES


def run(store, graph_id, node=None, radius=1, direction="both", include_center=True, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. ego_network takes graph_id, node, "
                     f"radius, direction, include_center and top_k.")
    err = check_node(g, node)
    if err:
        return err
    if isinstance(radius, bool) or not isinstance(radius, int) or not 1 <= radius <= MAX_RADIUS:
        return error(f"radius must be a whole number from 1 to {MAX_RADIUS}; got {radius!r}. "
                     f"Use radius=1 for the immediate network.")
    if direction not in DIRECTIONS:
        return error(f"direction must be one of {', '.join(DIRECTIONS)}; got {direction!r}.")
    if not isinstance(include_center, bool):
        return error(f"include_center must be true or false; got {include_center!r}.")
    k, err = check_top_k(top_k)
    if err:
        return err

    used_direction = direction if g.directed else "both"
    steps = _reachable(g, node, radius, used_direction)
    members = sorted(n for n in steps if n != node)
    keep = ([node] + members) if include_center else members

    who = f"{g.label(node)} ({node})"
    if not keep:
        return error(f"{who} has no neighbours in graph '{graph_id}', so its ego network is empty "
                     f"without the centre. Call again with include_center=true, or a larger radius.")

    sub_id = store.subgraph(graph_id, keep, f"Ego network of {who} in '{graph_id}' at radius {radius}")
    sub = store.get(sub_id)

    ranked = sorted(members, key=lambda n: (-len(sub.undirected_neighbors(n)), n))
    listed = [node_ref(g, n, links_inside=len(sub.undirected_neighbors(n)), steps_from_center=steps[n])
              for n in ranked[:k]]

    result = {
        "center": node_ref(g, node),
        "radius": radius,
        "direction": used_direction,
        "include_center": include_center,
        "alters": len(members),
        "nodes": sub.number_of_nodes(),
        "edges": sub.number_of_edges(),
        "density": round(_density(sub), 6),
        "members_shown": len(listed),
        "members": listed,
        "graph_id": sub_id,
    }
    reach = "immediate neighbours" if radius == 1 else f"nodes within {radius} steps"
    summary = (f"The ego network of {who} in '{graph_id}' ({reach}, direction '{used_direction}') has "
               f"{sub.number_of_nodes()} nodes and {sub.number_of_edges()} edges, density "
               f"{result['density']:.3f}. It is registered as graph '{sub_id}'.")

    # Long labels can push a large listing over the 8 KB limit, so drop the least connected first.
    while result["members"] and not _fits(result, summary, sub_id):
        result["members"].pop()
        result["members_shown"] = len(result["members"])
    return ok(result, summary, result_graph_id=sub_id)
