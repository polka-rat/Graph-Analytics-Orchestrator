"""shortest_path_weighted: cheapest path between two nodes using Dijkstra's algorithm.

Edge weights are the costs (for 'airports' the distance in km). Follows edge direction on
directed graphs. Returns the total weight, the number of hops and the path itself.
"""
import heapq

from graphkit.contract import check_node, error, get_graph, node_ref, ok

MAX_PATH_NODES = 40  # keeps the response well under the 8 KB limit; longer paths are shortened


def run(store, graph_id, source=None, target=None, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. shortest_path_weighted takes "
                     f"graph_id, source and target.")
    if source is None or target is None:
        return error("Give both 'source' and 'target' node ids. Use lookup_node to find node ids from names.")
    err = check_node(g, source, "source") or check_node(g, target, "target")
    if err:
        return err
    for u, v, w in g.edges():
        if w < 0:
            return error(f"Graph '{graph_id}' has a negative edge weight ({u}->{v}: {w}); "
                         f"Dijkstra's algorithm needs non-negative weights.")

    # Dijkstra with a binary heap. Heap entries are (distance, node id): equal distances are
    # settled in node-id order, so the result is deterministic.
    dist = {source: 0.0}
    prev = {}
    done = set()
    heap = [(0.0, source)]
    while heap:
        d, u = heapq.heappop(heap)
        if u in done:
            continue
        done.add(u)
        if u == target:
            break
        for v, w in g.out_neighbors(u).items():
            nd = d + w
            if v not in done and (v not in dist or nd < dist[v]):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, v))

    if target not in done:
        return error(f"No path from '{source}' to '{target}' in '{graph_id}'"
                     f"{' (following edge directions)' if g.directed else ''}. "
                     f"Use reachability to check connectivity.")

    path = [target]
    while path[-1] != source:
        path.append(prev[path[-1]])
    path.reverse()

    total = round(dist[target], 6)
    hops = len(path) - 1
    shown = path
    truncated = len(path) > MAX_PATH_NODES
    if truncated:
        half = MAX_PATH_NODES // 2
        shown = path[:half] + path[-half:]
    result = {
        "source": node_ref(g, source),
        "target": node_ref(g, target),
        "distance": total,
        "hops": hops,
        "path": [node_ref(g, n) for n in shown],
    }
    if truncated:
        result["path_truncated"] = True

    src, dst = g.label(source), g.label(target)
    if source == target:
        summary = f"{src} ({source}) is the source and the target, so the shortest path has weight 0."
    else:
        route = " -> ".join(path) if len(path) <= 8 else f"{path[0]} -> ... -> {path[-1]}"
        word = "hop" if hops == 1 else "hops"
        summary = (f"The shortest path from {src} ({source}) to {dst} ({target}) has total weight {total} "
                   f"over {hops} {word}: {route}.")
    return ok(result, summary)
