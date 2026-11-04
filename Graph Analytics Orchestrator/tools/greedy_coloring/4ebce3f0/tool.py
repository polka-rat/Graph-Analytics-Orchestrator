"""Colours the nodes of a graph greedily so that no two neighbours share a colour.

Algorithm: put the nodes in an order chosen by the strategy, then give each node the smallest
colour (0, 1, 2, ...) that none of its already-coloured neighbours uses. The number of colours
used is an upper bound on the chromatic number. Edge direction is ignored.

Strategies:
- largest_first: nodes by degree, highest first. Time O(V log V + E).
- dsatur: next node is the uncoloured one with the most distinct colours among its neighbours
  (saturation), ties by degree. Time O(V^2 + E).
- smallest_last: repeatedly remove a node of smallest remaining degree; colour in the reverse
  of the removal order. Time O(V^2 + E) here.
Ties keep the graph's node order (as NetworkX does); smallest_last breaks ties by node id.
"""
import json

from graphkit.contract import MAX_OUTPUT_BYTES, check_node, check_top_k, error, get_graph, node_ref, ok

STRATEGIES = ("largest_first", "dsatur", "smallest_last")
MEMBER_FLOOR = (10, 5, 3, 1, 0)  # members listed per colour, lowered until the output fits


def _neighbours(g):
    """Undirected neighbour sets, without self-loops."""
    return {u: set(g.undirected_neighbors(u)) - {u} for u in g.nodes()}


def _smallest_colour(u, nbrs, colour):
    used = {colour[v] for v in nbrs[u] if v in colour}
    c = 0
    while c in used:
        c += 1
    return c


def _largest_first(nodes, nbrs, colour):
    # sorted() is stable, so nodes with the same degree keep the graph's node order.
    for u in sorted(nodes, key=lambda n: len(nbrs[n]), reverse=True):
        colour[u] = _smallest_colour(u, nbrs, colour)


def _dsatur(nodes, nbrs, colour):
    seen_colours = {u: set() for u in nodes}  # distinct colours among each node's coloured neighbours
    uncoloured = list(nodes)
    while uncoloured:
        # max() returns the first best node, so ties keep the graph's node order.
        u = max(uncoloured, key=lambda n: (len(seen_colours[n]), len(nbrs[n])))
        uncoloured.remove(u)
        c = _smallest_colour(u, nbrs, colour)
        colour[u] = c
        for v in nbrs[u]:
            seen_colours[v].add(c)


def _smallest_last(nodes, nbrs, colour):
    remaining = {u: set(nbrs[u]) for u in nodes}
    removed = []
    while remaining:
        u = min(remaining, key=lambda n: (len(remaining[n]), n))
        removed.append(u)
        for v in remaining.pop(u):
            remaining[v].discard(u)
    for u in reversed(removed):
        colour[u] = _smallest_colour(u, nbrs, colour)


def _build(g, classes, cap, num_colours, strategy, max_degree, node, colour):
    result = {
        "num_colors": num_colours,
        "strategy": strategy,
        "valid": True,
        "max_degree": max_degree,
        "color_classes": [
            {"color": c, "size": len(members),
             "members": [node_ref(g, n) for n in members[:cap]],
             "members_shown": min(cap, len(members))}
            for c, members in enumerate(classes)
        ],
    }
    if node is not None:
        result["node"] = node_ref(g, node, color=colour[node])
    return result


def run(store, graph_id, strategy="largest_first", top_k=10, node=None, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     f"greedy_coloring takes graph_id, strategy, top_k and node.")
    if strategy not in STRATEGIES:
        return error(f"strategy must be one of {', '.join(STRATEGIES)}; got {strategy!r}.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if node is not None:
        err = check_node(g, node)
        if err:
            return err
    nodes = g.nodes()
    if not nodes:
        return error(f"Graph '{graph_id}' has no nodes to colour. Use list_graphs to pick a non-empty graph.")

    nbrs = _neighbours(g)
    colour = {}
    {"largest_first": _largest_first, "dsatur": _dsatur, "smallest_last": _smallest_last}[strategy](
        nodes, nbrs, colour)

    # Check the colouring: no edge may join two nodes of the same colour.
    clashes = sum(1 for u in nodes for v in nbrs[u] if colour[u] == colour[v])
    if clashes:
        return error(f"Internal error: the colouring has {clashes // 2} clashing edges.")

    num_colours = max(colour.values()) + 1
    classes = [sorted(n for n in nodes if colour[n] == c) for c in range(num_colours)]
    max_degree = max(len(nbrs[u]) for u in nodes)

    # Keep the output under 8 KB: list at most top_k members per colour, fewer if needed.
    budget = MAX_OUTPUT_BYTES - 1000
    result = None
    for cap in [k] + [c for c in MEMBER_FLOOR if c < k]:
        result = _build(g, classes, cap, num_colours, strategy, max_degree, node, colour)
        if len(json.dumps(result).encode("utf-8")) <= budget:
            break

    sizes = ", ".join(str(len(c)) for c in classes[:10])
    summary = (f"A {strategy} greedy colouring of '{graph_id}' uses {num_colours} colour"
               f"{'' if num_colours == 1 else 's'} for {len(nodes)} nodes, so {num_colours} groups "
               f"(e.g. time slots) are enough to keep every pair of neighbours apart"
               f"{' (edge direction ignored)' if g.directed else ''}. Group sizes: {sizes}"
               f"{', ...' if num_colours > 10 else ''}.")
    if node is not None:
        summary += f" {g.label(node)} ({node}) gets colour {colour[node]}."
    return ok(result, summary)