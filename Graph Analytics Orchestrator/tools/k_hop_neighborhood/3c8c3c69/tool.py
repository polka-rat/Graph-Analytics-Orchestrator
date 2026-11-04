import json

from graphkit.contract import MAX_OUTPUT_BYTES, check_node, check_top_k, error, get_graph, node_ref, ok

DIRECTIONS = ("out", "in", "both")
OUTPUT_BUDGET = MAX_OUTPUT_BYTES - 256


def _hops_from(g, source, k, direction):
    if not g.directed or direction == "both":
        step = g.undirected_neighbors
    elif direction == "out":
        step = g.out_neighbors
    else:
        step = g.in_neighbors
    hops = {source: 0}
    frontier = [source]
    for depth in range(1, k + 1):
        next_frontier = []
        for u in frontier:
            for v in step(u):
                if v not in hops:
                    hops[v] = depth
                    next_frontier.append(v)
        if not next_frontier:
            break
        frontier = next_frontier
    return hops


def _size(out):
    return len(json.dumps(out, sort_keys=True).encode("utf-8"))


def run(store, graph_id, node=None, k=2, direction="out", top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     f"k_hop_neighborhood takes graph_id, node, k, direction and top_k.")
    err = check_node(g, node)
    if err:
        return err
    if isinstance(k, bool) or not isinstance(k, int) or k < 1:
        return error(f"k must be a whole number of hops, 1 or more (e.g. k=2 for 'within two hops'); got {k!r}.")
    if direction not in DIRECTIONS:
        return error(f"direction must be one of {', '.join(DIRECTIONS)}; got {direction!r}. "
                     f"Use 'out' to follow edges forwards, 'in' to follow them backwards, 'both' to ignore direction.")
    top_k, err = check_top_k(top_k)
    if err:
        return err

    hops = _hops_from(g, node, k, direction)
    found = []
    for n in hops:
        if n != node:
            found.append(n)
    found.sort(key=lambda n: (hops[n], n))
    counts = {}
    for n in found:
        counts[hops[n]] = counts.get(hops[n], 0) + 1
    per_hop = []
    for h in sorted(counts):
        per_hop.append({"hops": h, "count": counts[h]})

    if direction == "out":
        where = "along edge direction"
    elif direction == "in":
        where = "against edge direction"
    else:
        where = "ignoring edge direction"
    centre = f"{g.label(node)} ({node})"
    if g.directed:
        mode = where
        description = f"Nodes within {k} hop(s) of {centre} in '{graph_id}', {where}"
    else:
        mode = "undirected"
        description = f"Nodes within {k} hop(s) of {centre} in '{graph_id}'"
    sub_id = store.subgraph(graph_id, [node] + found, description)
    sub = store.get(sub_id)

    if not found:
        if g.directed and direction != "both":
            if direction == "out":
                kind = "outgoing"
            else:
                kind = "incoming"
            summary = (f"No other node is within {k} hop(s) of {centre} in '{graph_id}': it has no {kind} "
                       f"edges. Try direction='both' to ignore edge direction.")
        else:
            summary = f"No other node is within {k} hop(s) of {centre} in '{graph_id}': it has no neighbours."
        result = {"center": node_ref(g, node), "k": k, "direction": mode, "count": 0,
                  "per_hop": [], "nodes": []}
        return ok(result, summary, result_graph_id=sub_id)

    parts = []
    for e in per_hop:
        if e["hops"] > 1:
            parts.append(f"{e['count']} at {e['hops']} hops")
        else:
            parts.append(f"{e['count']} at {e['hops']} hop")
    breakdown = ", ".join(parts)
    shown = min(top_k, len(found))
    while True:
        nodes = []
        for n in found[:shown]:
            nodes.append(node_ref(g, n, hops=hops[n]))
        result = {"center": node_ref(g, node), "k": k, "direction": mode, "count": len(found),
                  "per_hop": per_hop, "nodes": nodes}
        if shown < len(found):
            listing = f"Listed: the {shown} nearest (by hops, then id)."
        else:
            listing = "All of them are listed."
        summary = (f"{len(found)} node(s) are within {k} hop(s) of {centre} in '{graph_id}' ({mode}): "
                   f"{breakdown}. {listing} With {node} they form subgraph '{sub_id}' "
                   f"({sub.number_of_nodes()} nodes, {sub.number_of_edges()} edges).")
        out = ok(result, summary, result_graph_id=sub_id)
        if _size(out) <= OUTPUT_BUDGET or shown == 0:
            return out
        shown -= 1
