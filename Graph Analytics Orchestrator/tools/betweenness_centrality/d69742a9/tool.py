"""Rank nodes by betweenness centrality using Brandes' algorithm."""
import heapq
from collections import deque

from graphkit.contract import check_top_k, error, get_graph, node_ref, ok


def _single_source(g, source):
    stack = []
    predecessors = {node: [] for node in g.nodes()}
    sigma = {node: 0.0 for node in g.nodes()}
    sigma[source] = 1.0
    if g.weighted:
        distances = {source: 0.0}
        queue = [(0.0, source)]
        while queue:
            distance, u = heapq.heappop(queue)
            if distance != distances[u]:
                continue
            stack.append(u)
            for v, weight in g.out_neighbors(u).items():
                if weight < 0:
                    raise ValueError("negative edge weights are not supported")
                candidate = distance + weight
                known = distances.get(v, float("inf"))
                if candidate < known:
                    distances[v] = candidate
                    heapq.heappush(queue, (candidate, v))
                    sigma[v] = sigma[u]
                    predecessors[v] = [u]
                elif candidate == known:
                    sigma[v] += sigma[u]
                    predecessors[v].append(u)
    else:
        distances = {source: 0}
        queue = deque([source])
        while queue:
            u = queue.popleft()
            stack.append(u)
            for v in g.out_neighbors(u):
                if v not in distances:
                    distances[v] = distances[u] + 1
                    queue.append(v)
                    sigma[v] = sigma[u]
                    predecessors[v] = [u]
                elif distances[v] == distances[u] + 1:
                    sigma[v] += sigma[u]
                    predecessors[v].append(u)

    dependency = {node: 0.0 for node in g.nodes()}
    while stack:
        w = stack.pop()
        if w == source:
            continue
        for v in predecessors[w]:
            dependency[v] += (sigma[v] / sigma[w]) * (1.0 + dependency[w])
    dependency[source] = 0.0
    return dependency


def run(store, graph_id: str, top_k=10, **params) -> dict:
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. betweenness_centrality takes graph_id and top_k.")
    k, err = check_top_k(top_k)
    if err:
        return err
    nodes = g.nodes()
    scores = {node: 0.0 for node in nodes}
    try:
        for source in nodes:
            contribution = _single_source(g, source)
            for node, value in contribution.items():
                scores[node] += value
    except ValueError as exc:
        return error(str(exc))
    n = len(nodes)
    if n > 2:
        factor = 1.0 / ((n - 1) * (n - 2))
        scores = {node: value * factor for node, value in scores.items()}
    else:
        scores = {node: 0.0 for node in nodes}
    top = sorted(scores.items(), key=lambda item: (-item[1], str(item[0])))[:k]
    result = [node_ref(g, node, score=round(score, 6)) for node, score in top]
    summary = (f"{result[0]['label']} has the highest betweenness centrality ({result[0]['score']}) "
               f"among {n} nodes." if result else "The graph has no nodes.")
    return ok(result, summary)

