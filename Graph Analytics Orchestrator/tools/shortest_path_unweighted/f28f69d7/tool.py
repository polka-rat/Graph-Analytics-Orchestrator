"""Find a fewest-hop path with breadth-first search."""

from collections import deque
import json

from graphkit.contract import MAX_OUTPUT_BYTES, check_node, error, get_graph, node_ref, ok


def run(store, graph_id, source=None, target=None, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(sorted(params))}. Use graph_id, source, and target.")
    for name, node in (("source", source), ("target", target)):
        err = check_node(g, node, name)
        if err:
            return err

    parents = {source: None}
    queue = deque([source])
    while queue and target not in parents:
        node = queue.popleft()
        for neighbor in sorted(g.out_neighbors(node)):
            if neighbor not in parents:
                parents[neighbor] = node
                queue.append(neighbor)

    if target not in parents:
        return error(f"No path from '{source}' to '{target}' in '{graph_id}'. "
                     "Try another destination or check the graph's edge directions.")

    path = []
    node = target
    while node is not None:
        path.append(node)
        node = parents[node]
    path.reverse()

    hops = len(path) - 1
    result = {"path": [node_ref(g, node) for node in path], "hops": hops}
    summary = (f"The shortest path from {g.label(source)} ({source}) to "
               f"{g.label(target)} ({target}) has {hops} hop{'s' if hops != 1 else ''}.")
    output = ok(result, summary)
    if len(json.dumps(output, sort_keys=True).encode("utf-8")) > MAX_OUTPUT_BYTES:
        return error("The path is too long for the 8 KB response limit. "
                     "Try endpoints that are closer together.")
    return output
