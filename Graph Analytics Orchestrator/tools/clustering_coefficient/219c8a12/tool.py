import json

from graphkit.contract import MAX_OUTPUT_BYTES, check_node, check_top_k, error, get_graph, node_ref, ok

TARGET_BYTES = min(7500, MAX_OUTPUT_BYTES)


def _neighbour_sets(g):
    nodes = g.nodes()
    index = {n: i for i, n in enumerate(nodes)}
    nbrs = [set() for _ in nodes]
    for u, v, _ in g.edges():
        if u != v:
            iu, iv = index[u], index[v]
            nbrs[iu].add(iv)
            nbrs[iv].add(iu)
    return nodes, nbrs


def _triangles(nbrs):
    n = len(nbrs)
    rank = sorted(range(n), key=lambda i: (len(nbrs[i]), i))
    pos = [0] * n
    for r, i in enumerate(rank):
        pos[i] = r
    forward = [{j for j in nbrs[i] if pos[j] > pos[i]} for i in range(n)]
    tri = [0] * n
    for u in range(n):
        fu = forward[u]
        for v in fu:
            for w in fu & forward[v]:
                tri[u] += 1
                tri[v] += 1
                tri[w] += 1
    return tri


def _coefficient(t, k):
    return 2.0 * t / (k * (k - 1)) if k >= 2 else 0.0


def _size(out):
    return len(json.dumps(out, allow_nan=False, sort_keys=True).encode("utf-8"))


def run(store, graph_id, node=None, top_k=10, min_degree=2, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. clustering_coefficient takes graph_id, "
                     f"node, top_k and min_degree.")
    if node is not None:
        err = check_node(g, node)
        if err:
            return err
    k, err = check_top_k(top_k)
    if err:
        return err
    if isinstance(min_degree, bool) or not isinstance(min_degree, int) or min_degree < 0:
        return error(f"min_degree must be a whole number of at least 0 (default 2); got {min_degree!r}.")
    if g.number_of_nodes() == 0:
        return error(f"Graph '{graph_id}' has no nodes, so there is nothing to measure. "
                     f"Use list_graphs to pick another graph.")

    nodes, nbrs = _neighbour_sets(g)
    tri = _triangles(nbrs)
    deg = [len(s) for s in nbrs]
    coef = [_coefficient(t, d) for t, d in zip(tri, deg)]
    n = len(nodes)
    average = sum(coef) / n
    triples = sum(d * (d - 1) // 2 for d in deg)
    transitivity = sum(tri) / triples if triples else 0.0

    caveats = [f"the graph average is {round(average, 6)} over all {n} nodes (nodes with fewer than 2 neighbours "
               f"count as 0) and global transitivity is {round(transitivity, 6)}"]
    if g.directed:
        caveats.append("edge direction was ignored (the graph is treated as undirected)")
    if g.weighted:
        caveats.append("edge weights were ignored")

    def summary(lead, extra=()):
        second = "; ".join(caveats + list(extra)) + "."
        return f"{lead} {second[0].upper()}{second[1:]}"

    def entry(i):
        return node_ref(g, nodes[i], score=round(coef[i], 6), degree=deg[i], triangles=tri[i])

    if node is not None:
        i = nodes.index(node)
        e = entry(i)
        if deg[i] < 2:
            why = (f"{e['label']} ({node}) has {deg[i]} neighbour{'s' if deg[i] != 1 else ''}, so no pair of "
                   f"neighbours can be connected: its clustering coefficient is defined as 0.")
        else:
            pairs = deg[i] * (deg[i] - 1) // 2
            why = (f"{e['label']} ({node}) has clustering coefficient {e['score']}: {tri[i]} of the {pairs} pairs "
                   f"among its {deg[i]} neighbours are connected to each other.")
        return ok([e], summary(why))

    if g.number_of_edges() == 0:
        return error(f"Graph '{graph_id}' has no edges, so every clustering coefficient is 0 and there is nothing "
                     f"to rank. Use list_graphs to pick a graph with edges.")
    eligible = [i for i in range(n) if deg[i] >= min_degree]
    if not eligible:
        return error(f"No node in '{graph_id}' has at least {min_degree} neighbours, so there is nothing to rank. "
                     f"Lower min_degree (default 2) or pick another graph.")

    ranked = sorted(eligible, key=lambda i: (-round(coef[i], 6), nodes[i]))
    shown = ranked[:k]
    while True:
        result = [entry(i) for i in shown]
        best = result[0]
        if coef[shown[0]] > 0:
            lead = (f"{best['label']} ({best['id']}) is the most clustered of {len(eligible)} nodes with at "
                    f"least {min_degree} neighbours (coefficient {best['score']}).")
        else:
            lead = (f"None of the {len(eligible)} nodes with at least {min_degree} neighbours is in a triangle, "
                    f"so every clustering coefficient is 0 (common in bipartite or tree-like graphs).")
        trimmed = []
        if len(shown) < min(k, len(ranked)):
            trimmed.append(f"only the top {len(shown)} nodes are listed to keep the response small")
        out = ok(result, summary(lead, trimmed))
        if _size(out) <= TARGET_BYTES or len(shown) == 1:
            return out
        shown = shown[:max(1, len(shown) * 3 // 4)]
