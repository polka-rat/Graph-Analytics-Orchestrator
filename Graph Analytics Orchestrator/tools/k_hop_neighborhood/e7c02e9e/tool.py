"""k_hop_neighborhood: every node within k steps of a start node, registered as a subgraph.

Breadth-first search that stops at depth k. O(V + E) in the worst case.
"""
import json
from collections import deque

from graphkit.contract import check_node, check_top_k, error, get_graph, node_ref, ok

DIRECTIONS = ("out", "in", "both")
MAX_RESULT_BYTES = 7000  # leave headroom under the 8 KB limit for the other output fields


def _as_int(value):
    """Accept 2 and 2.0 (LLMs often send floats), reject bools, text and fractions."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def run(store, graph_id, node=None, k=2, direction="out", top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err

    if params:
        return error(
            f"Unknown parameter(s): {', '.join(params)}. "
            "k_hop_neighborhood takes graph_id, node, k, direction and top_k."
        )

    if node is None:
        return error(
            "Give the start node in 'node' (a node id). "
            "Use lookup_node to find the id from a name."
        )

    err = check_node(g, node)
    if err:
        return err
    
    hops = _as_int(k)
    if hops is None or hops < 0:
        return error(f"k must be a whole number of hops, 0 or more; got {k!r}.")
    if direction not in DIRECTIONS:
        return error(f"direction must be one of {', '.join(DIRECTIONS)}; got {direction!r}.")
    limit, err = check_top_k(top_k)
    if err:
        return err

    # Which edges to follow. On undirected graphs every edge can be followed both ways.
    if not g.directed:
        neighbours, followed = g.out_neighbors, "undirected"
    elif direction == "out":
        neighbours, followed = g.out_neighbors, "outgoing"
    elif direction == "in":
        neighbours, followed = g.in_neighbors, "incoming"
    else:
        neighbours, followed = g.undirected_neighbors, "any-direction"

    dist = {node: 0}
    queue = deque([node])
    while queue:
        u = queue.popleft()
        if dist[u] == hops:
            continue
        for v in neighbours(u):
            if v not in dist:
                dist[v] = dist[u] + 1
                queue.append(v)

    reached = sorted((n for n in dist if n != node), key=lambda n: (dist[n], n))
    sub_id = store.subgraph(graph_id, [node] + reached,
                            f"{hops}-hop neighbourhood of {g.label(node)} ({node}) in '{graph_id}'")
    sub = store.get(sub_id)

    hop_counts = {}
    for n in reached:
        hop_counts[str(dist[n])] = hop_counts.get(str(dist[n]), 0) + 1
    shown = [node_ref(g, n, hops=dist[n]) for n in reached[:limit]]
    result = {"center": node_ref(g, node), "k": hops, "edges_followed": followed,
              "count": len(reached), "hop_counts": hop_counts,
              "subgraph_nodes": sub.number_of_nodes(), "subgraph_edges": sub.number_of_edges(),
              "nodes": shown, "truncated": len(reached) > len(shown)}
    while shown and len(json.dumps(result)) > MAX_RESULT_BYTES:  # long labels: stay under 8 KB
        shown = shown[:max(1, len(shown) // 2)] if len(shown) > 1 else []
        result["nodes"], result["truncated"] = shown, True

    where = f"'{graph_id}'" + ("" if followed == "undirected" else f" following {followed} edges")
    if not reached:
        summary = (f"No other node is within {hops} hop(s) of {g.label(node)} ({node}) in {where}; "
                   f"subgraph '{sub_id}' contains only that node.")
    else:
        summary = (f"{len(reached)} node(s) are within {hops} hop(s) of {g.label(node)} ({node}) in {where}. "
                   f"With the start node they form subgraph '{sub_id}' ({sub.number_of_nodes()} nodes, "
                   f"{sub.number_of_edges()} edges)"
                   + (f"; the nearest {len(shown)} are listed." if result["truncated"] else "."))
    return ok(result, summary, result_graph_id=sub_id)
