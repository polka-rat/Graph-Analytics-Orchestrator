"""Largest maximal cliques via Bron–Kerbosch with pivoting."""
from graphkit.contract import check_top_k, error, get_graph, node_ref, ok


def _undirected_adj(g):
    adj = {n: set() for n in g.nodes()}
    for u, v, _ in g.edges():
        if u == v:
            continue
        adj[u].add(v)
        adj[v].add(u)
    return adj


def _bron_kerbosch(adj):
    cliques = []

    def bk(r, p, x):
        if not p and not x:
            cliques.append(tuple(sorted(r)))
            return
        pivot = min(p | x, key=lambda u: (-len(p & adj[u]), u))
        for v in sorted(p - adj[pivot]):
            bk(r | {v}, p & adj[v], x & adj[v])
            p.remove(v)
            x.add(v)

    nodes = set(adj)
    if nodes:
        bk(set(), nodes, set())
    return cliques


def run(store, graph_id, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. maximal_cliques takes graph_id and top_k.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if g.directed:
        return error(
            f"'{graph_id}' is directed. maximal_cliques needs an undirected graph "
            "(karate, lesmis or projects). Directed clique notions are not supported."
        )

    adj = _undirected_adj(g)
    cliques = _bron_kerbosch(adj)
    cliques.sort(key=lambda c: (-len(c), c))
    max_size = len(cliques[0]) if cliques else 0
    chosen = cliques[:k]

    result_cliques = []
    result_graph_id = None
    for i, clique in enumerate(chosen):
        nodes = [node_ref(g, n) for n in clique]
        sub_id = None
        if clique:
            sub_id = store.subgraph(
                graph_id, list(clique),
                f"Maximal clique of size {len(clique)} in '{graph_id}'"
            )
        if i == 0:
            result_graph_id = sub_id
        result_cliques.append({"size": len(clique), "nodes": nodes, "graph_id": sub_id})

    result = {
        "max_size": max_size,
        "n_maximal": len(cliques),
        "cliques": result_cliques,
    }
    if not cliques:
        summary = f"'{graph_id}' has no nodes, so it has no cliques."
        return ok(result, summary)
    labels = ", ".join(g.label(n) for n in chosen[0][:5])
    extra = "..." if len(chosen[0]) > 5 else ""
    summary = (
        f"The largest clique in '{graph_id}' has {max_size} nodes ({labels}{extra}). "
        f"{len(cliques)} maximal clique(s) found; returning {len(chosen)}."
    )
    return ok(result, summary, result_graph_id)
