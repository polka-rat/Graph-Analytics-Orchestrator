import heapq
from graphkit.contract import check_node, error, get_graph, node_ref, ok

def run(store, graph_id: str, source: str = None, target: str = None, **params) -> dict:
    g, err = get_graph(store, graph_id)
    if err:
        return err

    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}.")

    err = check_node(g, source, param="source")
    if err:
        return err

    err = check_node(g, target, param="target")
    if err:
        return err

    nodes = list(g.nodes()) if callable(g.nodes) else list(g.nodes)
    edges = list(g.edges()) if callable(g.edges) else list(g.edges)

    adj = {n: [] for n in nodes}
    for e in edges:
        u, v = e[0], e[1]
        weight = 1.0
        if len(e) > 2 and isinstance(e[2], dict):
            weight = float(e[2].get("weight", 1.0))
        elif len(e) > 2 and isinstance(e[2], (int, float)):
            weight = float(e[2])

        if u in adj:
            adj[u].append((v, weight))
        if not g.directed and v in adj:
            adj[v].append((u, weight))

    # Dijkstra's Algorithm
    distances = {n: float("inf") for n in nodes}
    previous = {n: None for n in nodes}
    distances[source] = 0.0

    pq = [(0.0, source)]

    while pq:
        curr_dist, u = heapq.heappop(pq)

        if u == target:
            break

        if curr_dist > distances[u]:
            continue

        for v, w in adj.get(u, []):
            if distances[u] + w < distances[v]:
                distances[v] = distances[u] + w
                previous[v] = u
                heapq.heappush(pq, (distances[v], v))

    if distances[target] == float("inf"):
        return error(f"No path found between '{source}' and '{target}' in graph '{graph_id}'.")

    # Reconstruct path
    path = []
    curr = target
    while curr is not None:
        path.append(curr)
        curr = previous[curr]
    path.reverse()

    nodes_ref = [node_ref(g, n) for n in path]
    result = {
        "path": nodes_ref,
        "total_weight": round(distances[target], 6)
    }

    summary = f"Shortest path from '{source}' to '{target}' in graph '{graph_id}' has total weight {round(distances[target], 6)}."
    return ok(result, summary)
