import heapq
from collections import deque

from graphkit.contract import check_node, check_top_k, error, get_graph, node_ref, ok


def _bfs(adj, s, n):
    order, pred, sigma, dist = [], [[] for _ in range(n)], [0] * n, [-1] * n
    sigma[s], dist[s] = 1, 0
    queue = deque([s])
    while queue:
        v = queue.popleft()
        order.append(v)
        dv, sv = dist[v] + 1, sigma[v]
        for w in adj[v]:
            if dist[w] < 0:
                dist[w] = dv
                queue.append(w)
            if dist[w] == dv:
                sigma[w] += sv
                pred[w].append(v)
    return order, pred, sigma


def _dijkstra(adj, s, n):
    order, pred, sigma = [], [[] for _ in range(n)], [0] * n
    dist, seen = {}, {s: 0.0}
    sigma[s] = 1
    heap = [(0.0, 0, s, s)]
    counter = 1
    while heap:
        d, _, p, v = heapq.heappop(heap)
        if v in dist:
            continue
        sigma[v] += sigma[p] if p != v else 0
        order.append(v)
        dist[v] = d
        for w, length in adj[v]:
            vw = d + length
            if w not in dist and (w not in seen or vw < seen[w]):
                seen[w] = vw
                heapq.heappush(heap, (vw, counter, v, w))
                counter += 1
                sigma[w] = 0
                pred[w] = [v]
            elif vw == seen.get(w):
                sigma[w] += sigma[v]
                pred[w].append(v)
    return order, pred, sigma


def brandes(adj, n, weighted):
    bc = [0.0] * n
    shortest_paths = _dijkstra if weighted else _bfs
    for s in range(n):
        order, pred, sigma = shortest_paths(adj, s, n)
        delta = [0.0] * n
        while order:
            w = order.pop()
            coeff = (1.0 + delta[w]) / sigma[w]
            for v in pred[w]:
                delta[v] += sigma[v] * coeff
            if w != s:
                bc[w] += delta[w]
    return bc


def run(store, graph_id, top_k=10, normalized=True, weighted=False, node=None, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. betweenness_centrality takes "
                     f"graph_id, top_k, normalized, weighted and node.")
    k, err = check_top_k(top_k)
    if err:
        return err
    for pname, value in (("normalized", normalized), ("weighted", weighted)):
        if not isinstance(value, bool):
            return error(f"{pname} must be true or false; got {value!r}.")
    if node is not None:
        err = check_node(g, node)
        if err:
            return err
    nodes = sorted(g.nodes())
    n = len(nodes)
    if n == 0:
        return error(f"Graph '{graph_id}' has no nodes, so there is nothing to rank. Pick a non-empty graph.")

    use_weights = weighted and g.weighted
    if use_weights and any(w < 0 for _, _, w in g.edges()):
        return error(f"Graph '{graph_id}' has negative edge weights, which shortest paths cannot use. "
                     f"Call again with weighted=false to count hops instead.")

    idx = {v: i for i, v in enumerate(nodes)}
    if use_weights:
        adj = [[(idx[w], length) for w, length in g.out_neighbors(v).items() if w != v] for v in nodes]
    else:
        adj = [[idx[w] for w in g.out_neighbors(v) if w != v] for v in nodes]
    bc = brandes(adj, n, use_weights)

    if normalized:
        scale = 1.0 / ((n - 1) * (n - 2)) if n > 2 else 1.0
    else:
        scale = 1.0 if g.directed else 0.5
    scores = {v: bc[i] * scale for i, v in enumerate(nodes)}

    ranking = sorted(scores, key=lambda v: (-round(scores[v], 6), v))
    rank_of = {v: r for r, v in enumerate(ranking, 1)}
    picked = [node] if node is not None else ranking[:k]
    result = [node_ref(g, v, score=round(scores[v], 6), rank=rank_of[v]) for v in picked]

    paths = "edge-weight (distance)" if use_weights else "hop-count"
    how = f"{'normalised' if normalized else 'raw'} betweenness on {paths} shortest paths"
    note = " (the graph is unweighted, so hops were counted)" if weighted and not g.weighted else ""
    top = result[0]
    if node is not None:
        summary = (f"{top['label']} ({top['id']}) has {how} of {top['score']}{note}, "
                   f"ranking {top['rank']} of {n} nodes.")
    elif top["score"] == 0:
        summary = (f"Every node in '{graph_id}' has betweenness 0{note}: no node lies on a shortest path "
                   f"between two other nodes.")
    else:
        summary = (f"{top['label']} ({top['id']}) lies on the most shortest paths in '{graph_id}', with "
                   f"{how} of {top['score']}{note}; the top {len(result)} of {n} nodes are listed.")
    return ok(result, summary)
