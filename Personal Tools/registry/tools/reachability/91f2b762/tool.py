"""reachability: is there any path from one node to another? (breadth-first search)

Follows edge direction on directed graphs and works on undirected graphs too.
Also reports the fewest hops when a path exists.
"""
from collections import deque

from graphkit.contract import check_node, error, get_graph, node_ref, ok


def run(store, graph_id, source=None, target=None, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. reachability takes graph_id, source and target.")
    if source is None or target is None:
        return error("Give both 'source' and 'target' node ids. Use lookup_node to find node ids from names.")
    err = check_node(g, source, "source") or check_node(g, target, "target")
    if err:
        return err

    # Breadth-first search from source, following edges in their direction.
    # BFS reaches nodes in order of hop count, so the first time we see target is its fewest-hop distance.
    hops = {source: 0}
    queue = deque([source])
    while queue and target not in hops:
        u = queue.popleft()
        for v in g.out_neighbors(u):
            if v not in hops:
                hops[v] = hops[u] + 1
                queue.append(v)

    reachable = target in hops
    result = {
        "source": node_ref(g, source),
        "target": node_ref(g, target),
        "reachable": reachable,
        "hops": hops[target] if reachable else None,
    }
    src, dst = g.label(source), g.label(target)
    direction = "following edge directions" if g.directed else "in this undirected graph"
    if not reachable:
        summary = f"No path exists from {src} ({source}) to {dst} ({target}) {direction}."
    elif source == target:
        summary = f"{src} ({source}) is the same node as the target, so it is trivially reachable (0 hops)."
    else:
        word = "hop" if hops[target] == 1 else "hops"
        summary = f"Yes: {dst} ({target}) is reachable from {src} ({source}) in {hops[target]} {word} at the fewest."
    return ok(result, summary)
