"""Compute graph diameter, node eccentricities, center, and periphery."""
import heapq
from collections import deque

from graphkit.contract import check_top_k, error, get_graph, node_ref, ok


def _distances(g, source):
    if not g.weighted:
        distances = {source: 0.0}
        queue = deque([source])
        while queue:
            u = queue.popleft()
            for v in g.out_neighbors(u):
                if v not in distances:
                    distances[v] = distances[u] + 1.0
                    queue.append(v)
        return distances
    distances = {source: 0.0}
    heap = [(0.0, source)]
    while heap:
        distance, u = heapq.heappop(heap)
        if distance != distances[u]:
            continue
        for v, weight in g.out_neighbors(u).items():
            if weight < 0:
                raise ValueError("negative edge weights are not supported")
            candidate = distance + weight
            if candidate < distances.get(v, float("inf")):
                distances[v] = candidate
                heapq.heappush(heap, (candidate, v))
    return distances


def run(store, graph_id: str, top_k=10, **params) -> dict:
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. diameter_eccentricity takes graph_id and top_k.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if g.number_of_nodes() == 0:
        return error("The graph is empty; provide a graph with at least one node.")

    try:
        eccentricity = {}
        distances_by_node = {}
        for source in g.nodes():
            distances = _distances(g, source)
            if len(distances) != g.number_of_nodes():
                return error("Diameter is undefined for a disconnected graph.")
            distances_by_node[source] = distances
            eccentricity[source] = max(distances.values(), default=0.0)
    except ValueError as exc:
        return error(str(exc))

    diameter = max(eccentricity.values(), default=0.0)
    centers = sorted((n for n, value in eccentricity.items() if value == min(eccentricity.values())), key=str)
    periphery = sorted((n for n, value in eccentricity.items() if value == diameter), key=str)
    ranked = sorted(eccentricity.items(), key=lambda item: (-item[1], str(item[0])))[:k]
    result = {
        "diameter": round(diameter, 6),
        "eccentricity": [node_ref(g, n, score=round(value, 6)) for n, value in ranked],
        "center": [node_ref(g, n) for n in centers[:k]],
        "periphery": [node_ref(g, n) for n in periphery[:k]],
    }
    summary = (f"The graph diameter is {result['diameter']}; its center has {len(centers)} node(s) "
               f"and its periphery has {len(periphery)} node(s).")
    return ok(result, summary)

