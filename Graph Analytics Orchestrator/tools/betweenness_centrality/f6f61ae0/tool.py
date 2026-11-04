"""Exact Brandes betweenness, using BFS or positive-weight Dijkstra."""
from collections import deque
from heapq import heappop, heappush
import json
import math
from graphkit.contract import check_top_k, error, get_graph, node_ref, ok


def run(store, graph_id=None, top_k=10, normalized=True, weighted=False, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. Use graph_id, top_k, normalized and weighted.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if not isinstance(normalized, bool) or not isinstance(weighted, bool):
        return error("normalized and weighted must be booleans (true or false).")
    nodes = sorted(g.nodes())
    adjacency = {u: dict(g.out_neighbors(u)) for u in nodes}
    if weighted and any(not math.isfinite(w) or w <= 0 for ns in adjacency.values() for w in ns.values()):
        return error("Weighted betweenness requires finite, strictly positive edge lengths. Use weighted=false to ignore weights.")
    scores = dict.fromkeys(nodes, 0.0)
    for source in nodes:
        predecessors = {u: [] for u in nodes}
        sigma = dict.fromkeys(nodes, 0)
        sigma[source] = 1
        distance = {source: 0}
        order = []
        if weighted:
            queue = [(0, source)]
            settled = set()
            while queue:
                dist, u = heappop(queue)
                if u in settled:
                    continue
                settled.add(u)
                order.append(u)
                for v, weight in adjacency[u].items():
                    candidate = dist + weight
                    if not math.isfinite(candidate):
                        return error("Path lengths overflow; rescale edge weights or use weighted=false.")
                    if v not in distance or candidate < distance[v]:
                        distance[v] = candidate
                        sigma[v] = sigma[u]
                        predecessors[v] = [u]
                        heappush(queue, (candidate, v))
                    elif candidate == distance[v]:
                        sigma[v] += sigma[u]
                        predecessors[v].append(u)
        else:
            queue = deque([source])
            while queue:
                u = queue.popleft()
                order.append(u)
                for v in adjacency[u]:
                    if v not in distance:
                        distance[v] = distance[u] + 1
                        queue.append(v)
                    if distance[v] == distance[u] + 1:
                        sigma[v] += sigma[u]
                        predecessors[v].append(u)
        dependency = dict.fromkeys(nodes, 0.0)
        for v in reversed(order):
            for u in predecessors[v]:
                dependency[u] += (sigma[u] / sigma[v]) * (1 + dependency[v])
            if v != source:
                scores[v] += dependency[v]
    n = len(nodes)
    scale = 1 / ((n - 1) * (n - 2)) if normalized and n > 2 else (1 if g.directed else 0.5)
    scores = {u: round(value * scale, 6) for u, value in scores.items()}
    result = [node_ref(g, u, score=scores[u])
              for u in sorted(nodes, key=lambda u: (-scores[u], u))[:k]]
    summary = (f"Ranked {n} nodes by {'normalized' if normalized else 'unnormalized'} betweenness centrality, excluding endpoints. "
               f"Showing up to {k} nodes using {'weighted' if weighted else 'unweighted'} shortest paths.")
    out = ok(result, summary)
    while len(json.dumps(out).encode()) > 8192 and result:
        result.pop()
    if n and not result:
        return error("Node labels exceed the response size limit; use shorter labels.")
    return out
