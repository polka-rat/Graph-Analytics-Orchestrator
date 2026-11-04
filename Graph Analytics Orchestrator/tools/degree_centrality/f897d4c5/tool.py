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
    N = len(nodes)
    if N <= 1:
        centralities = {n: 0.0 for n in nodes}
    else:
        edges = list(g.edges()) if callable(g.edges) else list(g.edges)
        degrees = {n: 0 for n in nodes}
        
        for e in edges:
            u, v = e[0], e[1]
            if u in degrees:
                degrees[u] += 1
            if v in degrees and not g.directed:
                degrees[v] += 1

        scale = 1.0 / (N - 1)
        centralities = {n: degrees[n] * scale for n in nodes}

    sorted_nodes = sorted(centralities.items(), key=lambda x: x[1], reverse=True)[:k]

    result = [
        node_ref(g, node, centrality=round(score, 6))
        for node, score in sorted_nodes
    ]

    summary = f"Top {len(result)} nodes by degree centrality in graph '{graph_id}'."
    return ok(result, summary)
