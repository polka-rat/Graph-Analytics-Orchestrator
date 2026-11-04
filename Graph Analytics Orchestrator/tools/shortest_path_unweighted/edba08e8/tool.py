"""shortest_path_unweighted: fewest-hop path between two nodes using breadth-first search.

Edge weights are ignored. On directed graphs edges are followed in their direction.
"""
from collections import deque

from graphkit.contract import check_node, error, get_graph, node_ref, ok

MAX_PATH_NODES = 60  # keeps the response far below the 8 KB limit


def run(store, graph_id, source=None, target=None, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. This tool takes graph_id, source and target.")
    if source is None or target is None:
        return error("Give both 'source' and 'target' node ids. Use lookup_node to find ids from names.")
    for value, name in ((source, "source"), (target, "target")):
        err = check_node(g, value, name)
        if err:
            return err

    src, dst = source, target
    parent = {src: None}
    if src != dst:
        queue = deque([src])
        found = False
        while queue and not found:
            u = queue.popleft()
            for v in sorted(g.out_neighbors(u)):  # sorted: deterministic tie-breaking
                if v not in parent:
                    parent[v] = u
                    if v == dst:
                        found = True
                        break
                    queue.append(v)

    s_ref, t_ref = node_ref(g, src), node_ref(g, dst)
    if dst not in parent:
        kind = "directed " if g.directed else ""
        return error(f"No path exists from {s_ref['label']} ({src}) to {t_ref['label']} ({dst}) in the "
                     f"{kind}graph '{graph_id}'. Check both ids with lookup_node, or try the reverse "
                     f"direction or another graph.")

    path = []
    cur = dst
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    hops = len(path) - 1

    shown = path
    truncated = len(path) > MAX_PATH_NODES
    if truncated:
        shown = path[:MAX_PATH_NODES - 1] + [path[-1]]
    result = {"reachable": True, "hops": hops, "source": s_ref, "target": t_ref,
              "path": [node_ref(g, n) for n in shown]}
    if truncated:
        result["path_truncated"] = True
    if hops == 0:
        summary = f"Source and target are the same node, {s_ref['label']} ({src}); the path has 0 hops."
    else:
        summary = (f"The shortest path from {s_ref['label']} ({src}) to {t_ref['label']} ({dst}) has "
                   f"{hops} hop{'s' if hops != 1 else ''}: " + " -> ".join(shown) + ".")
    return ok(result, summary)
