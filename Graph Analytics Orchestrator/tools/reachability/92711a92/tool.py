"""reachability: does any path lead from a source node to a target node?

Breadth-first search from the source. On a directed graph it follows edge
direction (unless ignore_direction is true). Returns yes/no, the fewest-hop
path when one exists, and how many nodes the source can reach. O(V + E).
"""
from collections import deque

from graphkit.contract import check_node, error, get_graph, node_ref, ok

MAX_PATH_NODES = 50  # keeps the output well under 8 KB


def _neighbours(g, node, ignore_direction):
    if g.directed and ignore_direction:
        return g.undirected_neighbors(node)
    return g.out_neighbors(node)


def run(store, graph_id, source=None, target=None, ignore_direction=False, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     "reachability takes graph_id, source, target and ignore_direction.")
    err = check_node(g, source, "source") or check_node(g, target, "target")
    if err:
        return err
    if not isinstance(ignore_direction, bool):
        return error(f"ignore_direction must be true or false; got {ignore_direction!r}.")

    # BFS from source, remembering each node's parent so the path can be rebuilt.
    parent = {source: None}
    queue = deque([source])
    while queue:
        u = queue.popleft()
        for v in sorted(_neighbours(g, u, ignore_direction)):  # sorted: deterministic path
            if v not in parent:
                parent[v] = u
                queue.append(v)

    reachable = target in parent
    n_reach = len(parent) - 1  # nodes reachable from source, not counting itself
    src_ref, tgt_ref = node_ref(g, source), node_ref(g, target)
    mode = " (ignoring edge direction)" if g.directed and ignore_direction else ""

    if not reachable:
        result = {"reachable": False, "source": src_ref, "target": tgt_ref, "hops": None, "path": [],
                  "nodes_reachable_from_source": n_reach}
        summary = (f"No: there is no path from {src_ref['label']} to {tgt_ref['label']}{mode}. "
                   f"{src_ref['label']} can reach {n_reach} of the other {g.number_of_nodes() - 1} nodes.")
        return ok(result, summary)

    path = [target]
    while parent[path[-1]] is not None:
        path.append(parent[path[-1]])
    path.reverse()
    hops = len(path) - 1
    shown = path if len(path) <= MAX_PATH_NODES else path[:MAX_PATH_NODES - 1] + [path[-1]]

    result = {"reachable": True, "source": src_ref, "target": tgt_ref, "hops": hops,
              "path": [node_ref(g, n) for n in shown], "path_truncated": len(shown) < len(path),
              "nodes_reachable_from_source": n_reach}
    if hops == 0:
        summary = f"Yes: {src_ref['label']} is the same node as the target, so it is trivially reachable."
    else:
        summary = (f"Yes: {tgt_ref['label']} is reachable from {src_ref['label']}{mode}, "
                   f"in {hops} hop{'s' if hops != 1 else ''} at the fewest.")
    return ok(result, summary)
