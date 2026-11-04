
"""Calculate closeness centrality scores for graph nodes."""

from collections import deque

from graphkit.contract import check_top_k, error, get_graph, node_ref, ok


def run(store, graph_id, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err

    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}.")

    k, err = check_top_k(top_k)
    if err:
        return err

    nodes = g.nodes()
    n = len(nodes)

    if n == 0:
        return error("The graph has no nodes to analyse.")

    scores = {}

    for source in nodes:
        distances = {source: 0}
        queue = deque([source])

        while queue:
            current = queue.popleft()

            if g.directed:
                neighbours = g.out_neighbors(current)
            else:
                neighbours = g.undirected_neighbors(current)

            for neighbour in neighbours:
                if neighbour not in distances:
                    distances[neighbour] = distances[current] + 1
                    queue.append(neighbour)

        reachable_count = len(distances) - 1
        total_distance = sum(distances.values())

        if reachable_count == 0 or total_distance == 0:
            scores[source] = 0.0
        else:
            scores[source] = reachable_count / total_distance

    top = sorted(
        scores.items(),
        key=lambda item: (-item[1], item[0])
    )[:k]

    result = [
        node_ref(g, node, score=round(score, 6))
        for node, score in top
    ]

    best = result[0]
    summary = (
        f"{best['label']} has the highest closeness centrality "
        f"({best['score']}) among {n} nodes."
    )

    return ok(result, summary)
