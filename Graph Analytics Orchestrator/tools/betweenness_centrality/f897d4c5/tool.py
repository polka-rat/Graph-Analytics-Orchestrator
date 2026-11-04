from collections import deque
from graphkit.contract import check_top_k, error, get_graph, node_ref, ok

def run(store, graph_id: str, top_k: int = 10, **params) -> dict:
    g, err = get_graph(store, graph_id)
    if err:
        return err

    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}.")

    k, err = check_top_k(top_k)
    if err:
        return err

    nodes = list(g.nodes()) if callable(g.nodes) else list(g.nodes)
    edges = list(g.edges()) if callable(g.edges) else list(g.edges)

    adj = {n: [] for n in nodes}
    for e in edges:
        u, v = e[0], e[1]
        if u in adj:
            adj[u].append(v)
        if not g.directed and v in adj:
            adj[v].append(u)

    cb = {n: 0.0 for n in nodes}

    # Brandes' Algorithm
    for s in nodes:
        S = []
        P = {w: [] for w in nodes}
        sigma = {w: 0 for w in nodes}
        sigma[s] = 1
        d = {w: -1 for w in nodes}
        d[s] = 0

        Q = deque([s])
        while Q:
            v = Q.popleft()
            S.append(v)
            for w in adj.get(v, []):
                if d[w] < 0:
                    Q.append(w)
                    d[w] = d[v] + 1
                if d[w] == d[v] + 1:
                    sigma[w] += sigma[v]
                    P[w].append(v)

        delta = {w: 0.0 for w in nodes}
        while S:
            w = S.pop()
            for v in P[w]:
                if sigma[w] != 0:
                    delta[v] += (sigma[v] / sigma[w]) * (1.0 + delta[w])
            if w != s:
                cb[w] += delta[w]

    # Normalization
    N = len(nodes)
    if not g.directed:
        for n in cb:
            cb[n] /= 2.0

    if N > 2:
        scale = 1.0 / ((N - 1) * (N - 2)) if g.directed else 2.0 / ((N - 1) * (N - 2))
        for n in cb:
            cb[n] *= scale

    sorted_nodes = sorted(cb.items(), key=lambda x: x[1], reverse=True)[:k]

    result = [
        node_ref(g, node, centrality=round(score, 6))
        for node, score in sorted_nodes
    ]

    summary = f"Top {len(result)} nodes by betweenness centrality in graph '{graph_id}'."
    return ok(result, summary)
