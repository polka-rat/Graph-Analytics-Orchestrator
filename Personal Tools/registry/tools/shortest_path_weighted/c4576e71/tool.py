"""shortest_path_weighted: Dijkstra's algorithm, returning the cheapest path and its total weight."""
import heapq

from graphkit.contract import check_node, error, get_graph, node_ref, ok


def _dijkstra(g, source, target):
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
        for v in sorted(g.out_neighbors(u)):
            if v in done:
                continue
            nd = d + g.out_neighbors(u)[v]
            if v not in dist or nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, v))
    if target not in done:
        return None, None
    path = [target]
    while path[-1] != source:
        path.append(prev[path[-1]])
    path.reverse()
    return dist[target], path


def run(store, graph_id, source=None, target=None, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. shortest_path_weighted takes graph_id, source and target.")
    if source is None or target is None:
        return error("Give both 'source' and 'target' node ids. Use lookup_node to find node ids.")
    err = check_node(g, source, "source")
    if err:
        return err
    err = check_node(g, target, "target")
    if err:
        return err

    for u, v, w in g.edges():
        if w < 0:
            return error(f"Graph '{graph_id}' has a negative edge weight ({u} to {v}: {w}); "
                         f"Dijkstra's algorithm needs non-negative weights.")

    dist, path = _dijkstra(g, source, target)
    src_label, dst_label = g.label(source), g.label(target)
    if dist is None:
        direction = "directed " if g.directed else ""
        return error(f"No path from {src_label} ({source}) to {dst_label} ({target}) in the {direction}graph "
                     f"'{graph_id}'. They are not connected; try another pair of nodes.")

    steps = []
    total = 0.0
    for i, node in enumerate(path):
        if i:
            total += g.out_neighbors(path[i - 1])[node]
        steps.append(node_ref(g, node, distance_from_source=round(total, 6)))
    distance = round(dist, 6)
    hops = len(path) - 1
    result = {
        "source": node_ref(g, source),
        "target": node_ref(g, target),
        "distance": distance,
        "hops": hops,
        "path": steps,
    }
    unit = "" if g.weighted else " (the graph is unweighted, so every edge counts 1)"
    if hops == 0:
        summary = f"{src_label} ({source}) is the source and the target, so the distance is 0."
    else:
        summary = (f"The cheapest path from {src_label} ({source}) to {dst_label} ({target}) has total weight "
                   f"{distance} over {hops} edge{'s' if hops != 1 else ''}{unit}.")
    return ok(result, summary)
