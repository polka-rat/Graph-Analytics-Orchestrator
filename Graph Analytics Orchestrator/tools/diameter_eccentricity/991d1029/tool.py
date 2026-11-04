"""Diameter, radius, center and periphery of a graph from hop-count eccentricities (BFS from every node)."""
import json
from collections import deque

from graphkit.contract import check_node, check_top_k, error, get_graph, node_ref, ok


MAX_BYTES = 7000  # keep well under the 8 KB output limit


def _bfs(g, source):
    """Hop distances from source following edge direction (all edges if undirected)."""
    dist = {source: 0}
    queue = deque([source])
    while queue:
        u = queue.popleft()
        for v in g.out_neighbors(u):
            if v not in dist:
                dist[v] = dist[u] + 1
                queue.append(v)
    return dist


def run(store, graph_id, top_k=10, node=None, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. diameter_eccentricity takes graph_id, top_k and node.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if node is not None:
        err = check_node(g, node)
        if err:
            return err

    nodes = sorted(g.nodes())
    n = len(nodes)
    if n == 0:
        return error(f"Graph '{graph_id}' has no nodes, so diameter and eccentricity are undefined.")

    ecc, far = {}, {}
    for s in nodes:
        dist = _bfs(g, s)
        if len(dist) < n:
            kind = "strongly connected" if g.directed else "connected"
            hint = ("Every node must reach every other node by following edge directions. " if g.directed else "")
            finder = "strongly_connected_components" if g.directed else "connected_components"
            return error(f"Graph '{graph_id}' is not {kind}: from {g.label(s)} ({s}) only {len(dist)} of {n} nodes "
                         f"are reachable. {hint}Diameter and eccentricity are only defined on {kind} graphs; "
                         f"use {finder} to find a connected part, "
                         f"or pick a connected graph such as karate or lesmis.")
        e = max(dist.values())
        ecc[s] = e
        far[s] = min(v for v, d in dist.items() if d == e)

    diameter, radius = max(ecc.values()), min(ecc.values())
    center = [v for v in nodes if ecc[v] == radius]
    periphery = [v for v in nodes if ecc[v] == diameter]
    u = periphery[0]
    pair = [node_ref(g, u, eccentricity=diameter), node_ref(g, far[u], eccentricity=ecc[far[u]])]

    result = {
        "diameter": diameter,
        "radius": radius,
        "center_size": len(center),
        "periphery_size": len(periphery),
        "center": [node_ref(g, v) for v in center[:k]],
        "periphery": [node_ref(g, v) for v in periphery[:k]],
        "farthest_pair": pair,
    }
    while len(json.dumps(result)) > MAX_BYTES:  # long labels: shorten the longer list
        longer = "center" if len(result["center"]) >= len(result["periphery"]) else "periphery"
        result[longer].pop()
    summary = (f"'{graph_id}' has diameter {diameter} and radius {radius} (in hops): "
               f"{len(center)} center node{'s' if len(center) != 1 else ''} and "
               f"{len(periphery)} periphery node{'s' if len(periphery) != 1 else ''}. "
               f"{pair[0]['label']} to {pair[1]['label']} is a farthest pair, {diameter} hops apart.")
    if len(result["center"]) < min(k, len(center)) or len(result["periphery"]) < min(k, len(periphery)):
        summary += " Lists were shortened to fit the output limit."
    if node is not None:
        result["node"] = node_ref(g, node, eccentricity=ecc[node])
        summary += f" {g.label(node)} ({node}) has eccentricity {ecc[node]}."
    return ok(result, summary)
