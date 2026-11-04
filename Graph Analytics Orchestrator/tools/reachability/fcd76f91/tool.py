"""reachability: can we get from one node to another?

I run a BFS from the source. BFS goes level by level, so the first time it
reaches the target we also have a shortest (fewest-hop) path to show.
"""
from collections import deque

from graphkit.contract import check_node, error, get_graph, node_ref, ok

# Paths longer than this are cut down to their start and end, so the reply stays small.
MAX_PATH_NODES = 40


def bfs(g, source, target, ignore_direction):
    """BFS from source. Returns the parent of every visited node and whether target was found."""
    next_nodes = g.undirected_neighbors if ignore_direction else g.out_neighbors
    parent = {source: None}
    queue = deque([source])
    while queue:
        u = queue.popleft()
        if u == target:
            return parent, True
        # sorted() so that the same path comes back every time
        for v in sorted(next_nodes(u)):
            if v not in parent:
                parent[v] = u
                queue.append(v)
    return parent, target in parent


def build_path(parent, target):
    path = [target]
    while parent[path[-1]] is not None:
        path.append(parent[path[-1]])
    return path[::-1]


def run(store, graph_id, source=None, target=None, ignore_direction=False, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     f"reachability takes graph_id, source, target and ignore_direction.")
    if source is None or target is None:
        return error("Give both 'source' and 'target' node ids. Use lookup_node to find node ids from names.")
    for node, name in ((source, "source"), (target, "target")):
        err = check_node(g, node, name)
        if err:
            return err
    if not isinstance(ignore_direction, bool):
        return error(f"ignore_direction must be true or false; got {ignore_direction!r}.")

    follows_direction = g.directed and not ignore_direction
    parent, found = bfs(g, source, target, ignore_direction)
    src, dst = g.label(source), g.label(target)
    if follows_direction:
        mode = "following edge directions"
    elif g.directed:
        mode = "ignoring edge directions"
    else:
        mode = "undirected graph"

    if not found:
        others = len(parent) - 1
        result = {"reachable": False, "source": node_ref(g, source), "target": node_ref(g, target),
                  "hops": None, "path": [], "path_truncated": False,
                  "nodes_reachable_from_source": others, "directed": follows_direction}
        summary = (f"No: there is no path from {src} ({source}) to {dst} ({target}) in '{graph_id}' ({mode}); "
                   f"{src} can reach only {others} of the other {g.number_of_nodes() - 1} nodes.")
        if follows_direction:
            summary += " Set ignore_direction=true to ask whether they are connected at all."
        return ok(result, summary)

    path = build_path(parent, target)
    hops = len(path) - 1
    if len(path) > MAX_PATH_NODES:
        half = MAX_PATH_NODES // 2
        shown = path[:half] + path[-half:]
    else:
        shown = path

    result = {"reachable": True, "source": node_ref(g, source), "target": node_ref(g, target),
              "hops": hops, "path": [node_ref(g, n) for n in shown],
              "path_truncated": len(shown) < len(path), "directed": follows_direction}
    if hops == 0:
        summary = f"Yes: {src} ({source}) is the target itself, so it is trivially reachable (0 hops)."
    else:
        route = " -> ".join(path) if shown is path else f"{source} -> ... -> {target}"
        summary = (f"Yes: {dst} ({target}) is reachable from {src} ({source}) in '{graph_id}' ({mode}); "
                   f"the shortest route takes {hops} hop(s): {route}.")
    return ok(result, summary)
