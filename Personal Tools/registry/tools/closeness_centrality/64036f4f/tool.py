from collections import deque

from graphkit.contract import check_top_k, error, get_graph, node_ref, ok


def _distances_to(g, target):
    distances = {target: 0}
    queue = deque([target])
    while queue:
        node = queue.popleft()
        neighbors = g.in_neighbors(node) if g.directed else g.neighbors(node)
        for neighbor in neighbors:
            if neighbor not in distances:
                distances[neighbor] = distances[node] + 1
                queue.append(neighbor)
    return distances


def run(store, graph_id, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(
            f"Unknown parameter(s): {', '.join(sorted(params))}. "
            "closeness_centrality takes graph_id and top_k."
        )
    k, err = check_top_k(top_k)
    if err:
        return err

    n = g.number_of_nodes()
    scores = {}
    for node in g.nodes():
        distances = _distances_to(g, node)
        reachable = len(distances) - 1
        total_distance = sum(distances.values())
        if total_distance == 0 or n <= 1:
            score = 0.0
        else:
            score = (reachable / total_distance) * (reachable / (n - 1))
        scores[node] = score

    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:k]
    result = [node_ref(g, node, score=round(score, 6)) for node, score in ranked]
    if not result:
        return ok([], f"Graph '{graph_id}' has no nodes to rank by closeness centrality.")
    best = result[0]
    direction = " using incoming paths" if g.directed else ""
    summary = (
        f"{best['label']} ({best['id']}) has the highest closeness centrality{direction} "
        f"at {best['score']} among {n} nodes."
    )
    return ok(result, summary)
