"""Compute unweighted eccentricities, diameter, radius, center, and periphery."""

import json
from collections import deque

from graphkit.contract import check_node, check_top_k, error, get_graph, node_ref, ok


def _distances(start, adjacency):
    distance = {start: 0}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        step = distance[node] + 1
        for neighbour in adjacency[node]:
            if neighbour not in distance:
                distance[neighbour] = step
                queue.append(neighbour)
    return distance


def run(store, graph_id, node=None, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(sorted(params))}.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if node is not None:
        err = check_node(g, node)
        if err:
            return err

    nodes = sorted(g.nodes())
    if not nodes:
        return error("The graph is empty, so diameter and eccentricity are undefined. Choose a non-empty graph.")

    adjacency = {current: tuple(sorted(g.out_neighbors(current))) for current in nodes}
    eccentricity = {}
    for current in nodes:
        distance = _distances(current, adjacency)
        if len(distance) != len(nodes):
            condition = "strongly connected" if g.directed else "connected"
            return error(
                f"Graph '{graph_id}' is not {condition}; finite whole-graph diameter and "
                "eccentricities are undefined. Use a connected component or subgraph."
            )
        eccentricity[current] = max(distance.values(), default=0)

    diameter = max(eccentricity.values())
    radius = min(eccentricity.values())
    centers = [current for current in nodes if eccentricity[current] == radius]
    periphery = [current for current in nodes if eccentricity[current] == diameter]
    center_result = [node_ref(g, current, eccentricity=radius) for current in centers[:k]]
    periphery_result = [node_ref(g, current, eccentricity=diameter) for current in periphery[:k]]

    result = {
        "diameter": diameter,
        "radius": radius,
        "center": center_result,
        "center_count": len(centers),
        "center_truncated": len(centers) > len(center_result),
        "periphery": periphery_result,
        "periphery_count": len(periphery),
        "periphery_truncated": len(periphery) > len(periphery_result),
        "node": node_ref(g, node, eccentricity=eccentricity[node]) if node is not None else None,
    }

    while len(json.dumps(result, ensure_ascii=False).encode("utf-8")) > 7000:
        if len(periphery_result) >= len(center_result) and periphery_result:
            periphery_result.pop()
            result["periphery_truncated"] = True
        elif center_result:
            center_result.pop()
            result["center_truncated"] = True
        else:
            break

    direction = "directed" if g.directed else "undirected"
    summary = (
        f"Graph '{graph_id}' has unweighted {direction} diameter {diameter}, radius {radius}, "
        f"{len(centers)} center node(s), and {len(periphery)} periphery node(s)."
    )
    return ok(result, summary)
