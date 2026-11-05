"""Diameter and eccentricities using BFS or Dijkstra"""
from collections import deque
from heapq import heappop, heappush
import json
from math import isfinite

from graphkit.contract import MAX_OUTPUT_BYTES, check_top_k, error, get_graph, node_ref, ok


def _distances(adjacency, start, weighted):
    distances = {start: 0.0 if weighted else 0}
    if not weighted:
        queue = deque([start])
        while queue:
            u = queue.popleft()
            for v in adjacency[u]:
                if v not in distances:
                    distances[v] = distances[u] + 1
                    queue.append(v)
    else:
        queue = [(0.0, start)]
        while queue:
            distance, u = heappop(queue)
            if distance != distances[u]:
                continue
            for v, weight in adjacency[u].items():
                candidate = distance + weight
                if candidate < distances.get(v, float("inf")):
                    distances[v] = candidate
                    heappush(queue, (candidate, v))
    return distances


def run(store, graph_id, top_k=10, use_weights=False, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(sorted(params))}. See tool.json.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if not isinstance(use_weights, bool):
        return error("use_weights must be a boolean (true or false).")
    nodes = sorted(g.nodes())
    if not nodes:
        return error("An empty graph has no diameter. Choose a graph containing at least one node.")
    adjacency = {u: dict(g.out_neighbors(u)) for u in nodes}
    if use_weights and any(not isfinite(w) or w < 0
                           for neighbors in adjacency.values() for w in neighbors.values()):
        return error("Weighted distances require finite non-negative weights. Use another graph or use_weights=false.")
    eccentricities = {}
    for u in nodes:
        distances = _distances(adjacency, u, use_weights)
        if len(distances) != len(nodes):
            requirement = "strongly connected" if g.directed else "connected"
            return error(f"The graph must be {requirement} for a finite diameter. Select a connected component first.")
        eccentricities[u] = max(distances.values())
    diameter, radius = max(eccentricities.values()), min(eccentricities.values())
    if not isfinite(diameter):
        return error("Path distances overflowed. Use smaller finite weights or use_weights=false.")
    center = [n for n in nodes if eccentricities[n] == radius]
    periphery = [n for n in nodes if eccentricities[n] == diameter]
    ranked = sorted(nodes, key=lambda n: (-eccentricities[n], n))[:k]
    result = {"diameter": round(diameter, 6), "radius": round(radius, 6),
              "use_weights": use_weights, "node_count": len(nodes),
              "eccentricities": [node_ref(g, n, eccentricity=round(eccentricities[n], 6)) for n in ranked],
              "center": [node_ref(g, n) for n in center[:k]], "center_count": len(center),
              "periphery": [node_ref(g, n) for n in periphery[:k]], "periphery_count": len(periphery),
              "truncated": len(nodes) > k}
    unit = "weighted distance" if use_weights else "hops"
    out = ok(result, f"Diameter is {round(diameter, 6)} and radius is {round(radius, 6)} ({unit}); "
             f"{len(center)} centre nodes and {len(periphery)} periphery nodes. Each list shows at most {k} nodes.")
    if len(json.dumps(out, sort_keys=True).encode("utf-8")) > MAX_OUTPUT_BYTES:
        return error("Result exceeds 8 KB. Reduce top_k or use a smaller subgraph.")
    return out
