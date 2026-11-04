
"""Calculate closeness centrality for one specified node."""

import heapq
import math
from collections import deque

from graphkit.contract import check_node, error, get_graph, node_ref, ok


def run(store, graph_id: str, node: str = None, **params):
    """Return NetworkX-style closeness centrality for one node."""

    # 1. Get the graph.
    g, err = get_graph(store, graph_id)
    if err:
        return err

    # 2. Reject unsupported parameters.
    if params:
        names = ", ".join(sorted(params))
        return error(
            f"Unknown parameter(s): {names}. "
            "Supported parameters are graph_id and node."
        )

    # 3. Check that the requested node exists.
    err = check_node(g, node, param="node")
    if err:
        return err

    # 4. Validate edge distances for weighted graphs.
    if g.weighted:
        for u, v, weight in g.edges():
            if not math.isfinite(weight) or weight <= 0:
                return error(
                    f"Edge {u!r}->{v!r} has invalid distance {weight!r}. "
                    "All edge distances in a weighted graph must be finite "
                    "and strictly positive."
                )

    # 5. Calculate shortest distances TO the selected node.
    # For directed graphs, traverse incoming edges.
    # For undirected graphs, incoming and outgoing neighbors are equivalent.
    distances = {node: 0.0}

    if g.weighted:
        # Dijkstra's algorithm.
        heap = [(0.0, node)]

        while heap:
            current_distance, current = heapq.heappop(heap)

            if current_distance != distances[current]:
                continue

            for predecessor, weight in sorted(
                g.in_neighbors(current).items()
            ):
                candidate = current_distance + weight

                if (
                    predecessor not in distances
                    or candidate < distances[predecessor]
                ):
                    distances[predecessor] = candidate
                    heapq.heappush(
                        heap, (candidate, predecessor)
                    )

    else:
        # Breadth-first search: every edge has distance 1.
        queue = deque([node])

        while queue:
            current = queue.popleft()

            for predecessor in sorted(g.in_neighbors(current)):
                if predecessor not in distances:
                    distances[predecessor] = distances[current] + 1.0
                    queue.append(predecessor)

    # 6. Apply NetworkX's improved normalization.
    total_nodes = g.number_of_nodes()
    reachable_nodes = len(distances)

    if total_nodes <= 1 or reachable_nodes <= 1:
        score = 0.0
    else:
        distance_sum = sum(distances.values())

        score = (
            (reachable_nodes - 1) / distance_sum
        ) * (
            (reachable_nodes - 1) / (total_nodes - 1)
        )

    score = round(score, 6)

    # 7. Return the selected node and its score.
    result = node_ref(
        g,
        node,
        score=score,
        reachable_nodes=reachable_nodes - 1,
    )

    summary = (
        f"Closeness centrality of {g.label(node)} ({node}) "
        f"is {score}. "
        f"It can be reached from {reachable_nodes - 1} other nodes."
    )

    return ok(result, summary)
