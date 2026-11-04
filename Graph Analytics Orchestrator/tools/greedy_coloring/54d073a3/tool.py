"""greedy_coloring: greedy vertex colouring and the number of colours it uses.

Strategies: "largest_first" (Welsh-Powell: highest degree first) and "dsatur"
(Brelaz: always colour the node whose neighbours already use the most different colours).
Each node gets the smallest colour (0, 1, 2, ...) not used by an already coloured neighbour,
so adjacent nodes never share a colour. Edge direction and weight are ignored.
"""
import json

from graphkit.contract import MAX_OUTPUT_BYTES, check_top_k, error, get_graph, node_ref, ok

_STRATEGIES = ("largest_first", "dsatur")


def _largest_first_order(nodes, adj):
    # Highest degree first; ties broken by node id (ascending) for determinism.
    return sorted(nodes, key=lambda v: (-len(adj[v]), v))


def _colour_in_order(order, adj):
    colour = {}
    for v in order:
        used = {colour[u] for u in adj[v] if u in colour}
        c = 0
        while c in used:
            c += 1
        colour[v] = c
    return colour, order


def _dsatur(nodes, adj):
    colour = {}
    neighbour_colours = {v: set() for v in nodes}  # colours already present around each node
    order = []
    remaining = set(nodes)
    while remaining:
        # Most saturated node first, then highest degree, then smallest id.
        v = min(remaining, key=lambda x: (-len(neighbour_colours[x]), -len(adj[x]), x))
        c = 0
        while c in neighbour_colours[v]:
            c += 1
        colour[v] = c
        order.append(v)
        remaining.discard(v)
        for u in adj[v]:
            neighbour_colours[u].add(c)
    return colour, order


def run(store, graph_id, top_k=10, strategy="largest_first", **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     f"greedy_coloring takes graph_id, top_k and strategy.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if strategy not in _STRATEGIES:
        return error(f"strategy must be one of {', '.join(_STRATEGIES)}; got {strategy!r}.")

    nodes = g.nodes()
    n = len(nodes)
    if n == 0:
        return error(f"Graph '{graph_id}' has no nodes, so it cannot be coloured.")

    # Neighbour sets ignoring direction; a self-loop is skipped (a node cannot differ from itself).
    adj = {v: {u for u in g.undirected_neighbors(v) if u != v} for v in nodes}

    if strategy == "largest_first":
        colour, order = _colour_in_order(_largest_first_order(nodes, adj), adj)
    else:
        colour, order = _dsatur(nodes, adj)

    # Independent check that the colouring is proper (no edge joins two nodes of the same colour).
    proper = all(colour[u] != colour[v] for u in nodes for v in adj[u])
    if not proper:  # cannot happen; guards against a bug rather than returning a wrong answer
        return error("Internal check failed: the colouring is not proper.")

    num_colours = max(colour.values()) + 1
    sizes = [0] * num_colours
    for c in colour.values():
        sizes[c] += 1
    max_degree = max(len(adj[v]) for v in nodes)

    entries = [node_ref(g, v, color=colour[v], degree=len(adj[v])) for v in order[:k]]
    shown = len(entries)
    result = {
        "num_colors": num_colours,
        "strategy": strategy,
        "num_nodes": n,
        "max_degree": max_degree,
        "is_proper_coloring": True,
        "color_class_sizes": [{"color": c, "size": s} for c, s in enumerate(sizes)],
        "nodes": entries,
    }
    # Keep the response under the size limit: shorten the node list if needed.
    while shown > 1 and len(json.dumps(result)) > MAX_OUTPUT_BYTES - 500:
        shown -= 1
        result["nodes"] = entries[:shown]

    summary = (f"Greedy colouring ({strategy}) of '{graph_id}' uses {num_colours} colours for {n} nodes; "
               f"no two adjacent nodes share a colour.")
    if g.directed:
        summary += " Edge directions were ignored."
    summary += f" Listing the first {shown} nodes in colouring order."
    return ok(result, summary)
