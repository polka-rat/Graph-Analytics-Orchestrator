"""shortest_path_unweighted: fewest-hop path between two nodes, found by breadth-first search.

Edge weights are ignored (every edge counts as one hop). On a directed graph the path
follows edge direction. Ties between equally short paths are broken deterministically:
neighbours are visited in ascending node-id order, so the same input always gives the same path.
"""
import json
from collections import deque

from graphkit.contract import MAX_OUTPUT_BYTES, check_node, error, get_graph, node_ref, ok

SIZE_BUDGET = MAX_OUTPUT_BYTES - 700  # leave room for the summary and the other keys
KEEP_ENDS = 30  # nodes kept at each end if a very long path would exceed the size limit


def _bfs(g, source, target):
    """Return the node list of a fewest-hop path source -> target, or None if target is unreachable."""
    if source == target:
        return [source]
    parent = {source: None}
    queue = deque([source])
    while queue:
        u = queue.popleft()
        for v in sorted(g.out_neighbors(u)):
            if v in parent:
                continue
            parent[v] = u
            if v == target:
                path = [v]
                while parent[path[-1]] is not None:
                    path.append(parent[path[-1]])
                return path[::-1]
            queue.append(v)
    return None


def run(store, graph_id, source=None, target=None, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     f"shortest_path_unweighted takes graph_id, source and target.")
    err = check_node(g, source, "source") or check_node(g, target, "target")
    if err:
        return err

    path = _bfs(g, source, target)
    src_label, dst_label = g.label(source), g.label(target)
    if path is None:
        direction = " following edge direction" if g.directed else ""
        return error(f"No path from {src_label} ({source}) to {dst_label} ({target}) in '{graph_id}'"
                     f"{direction}: they are in different parts of the graph. "
                     f"Try swapping source and target, or pick two other nodes.")

    hops = len(path) - 1
    result = [node_ref(g, n, step=i) for i, n in enumerate(path)]
    note = ""
    if len(json.dumps(result)) > SIZE_BUDGET:  # only for extremely long paths
        result = result[:KEEP_ENDS] + result[-KEEP_ENDS:]
        note = f" The path is long, so only its first and last {KEEP_ENDS} nodes are listed."
    if hops == 0:
        summary = f"{src_label} ({source}) is both the source and the target, so the path has 0 hops."
    else:
        names = " -> ".join(g.label(n) for n in path) if len(path) <= 12 else (
            " -> ".join(g.label(n) for n in path[:5]) + " -> ... -> " + " -> ".join(g.label(n) for n in path[-5:]))
        summary = f"The fewest hops from {src_label} to {dst_label} is {hops}: {names}.{note}"
    return ok(result, summary)
