"""reachability: is there a path from node A to node B? (breadth-first search)

Respects edge direction on directed graphs. Returns the fewest-hop path as evidence.
"""
from collections import deque

from graphkit.contract import check_node, error, get_graph, node_ref, ok

MAX_PATH_NODES = 50  # keep the output small (8 KB limit)


def run(store, graph_id, source=None, target=None, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. reachability takes graph_id, source and target.")
    err = check_node(g, source, "source") or check_node(g, target, "target")
    if err:
        return err

    # BFS from source; neighbours are visited in sorted order so the path is deterministic.
    parent = {source: None}
    queue = deque([source])
    while queue and target not in parent:
        u = queue.popleft()
        for v in sorted(g.out_neighbors(u)):
            if v not in parent:
                parent[v] = u
                queue.append(v)

    kind = "directed" if g.directed else "undirected"
    src_ref, tgt_ref = node_ref(g, source), node_ref(g, target)
    if target not in parent:
        return ok({"reachable": False, "source": src_ref, "target": tgt_ref, "hops": None, "path": []},
                  f"No: {src_ref['label']} cannot reach {tgt_ref['label']} in the {kind} graph '{graph_id}'.")

    path = []
    node = target
    while node is not None:
        path.append(node)
        node = parent[node]
    path.reverse()
    hops = len(path) - 1
    shown = path if len(path) <= MAX_PATH_NODES else path[:MAX_PATH_NODES]
    result = {"reachable": True, "source": src_ref, "target": tgt_ref, "hops": hops,
              "path": [node_ref(g, n) for n in shown]}
    if len(shown) < len(path):
        result["path_truncated"] = True
    if hops == 0:
        summary = f"Yes: {src_ref['label']} is the same node as the target (0 hops)."
    else:
        word = "hop" if hops == 1 else "hops"
        summary = (f"Yes: {src_ref['label']} can reach {tgt_ref['label']} in the {kind} graph '{graph_id}'; "
                   f"the shortest route takes {hops} {word}.")
    return ok(result, summary)
