"""Local clustering coefficient of nodes and the graph's average clustering.

Undirected graphs use c(u) = 2 T(u) / (deg(u) (deg(u) - 1)), where T(u) is the number of
triangles through u. Directed graphs use Fagiolo's directed clustering (every orientation of a
triangle counts), and the weighted variant uses the geometric mean of the normalised edge
weights, so the values match networkx.clustering / networkx.average_clustering.

Rules (the validator checks them):
- Implement the algorithm yourself: standard library, NumPy and graphkit only.
- Get graphs only from the store; never open files, print, or use the network.
- Never crash: return error("what went wrong and how to fix it") instead.
- Return every node as node_ref(g, node, ...), so it has both an id and a label.
- Keep the output under 8 KB: respect top_k.
- Be deterministic: same input, same output.
"""
import json

import numpy as np

from graphkit.contract import MAX_OUTPUT_BYTES, check_node, check_top_k, error, get_graph, node_ref, ok

# Leave room below the 8 KB limit for the summary and the JSON keys.
_SIZE_BUDGET = MAX_OUTPUT_BYTES - 400


def _clustering(g, weighted):
    """Return (nodes, clustering, degree, triangles) as parallel lists/arrays.

    With A the 0/1 adjacency matrix (or the cube root of the max-normalised weights when
    weighted) and S = A + A^T for directed graphs (S = A for undirected ones):
      undirected: c(u) = (S^3)_uu / (deg(deg - 1))                       [ (S^3)_uu = 2 T(u) ]
      directed:   c(u) = (S^3)_uu / (2 (d_tot (d_tot - 1) - 2 d_recip))   (Fagiolo 2007)
    Self-loops are ignored, as in NetworkX.
    """
    nodes = g.nodes()
    index = {n: i for i, n in enumerate(nodes)}
    n = len(nodes)
    adj = np.zeros((n, n))
    wts = np.zeros((n, n))
    for u in nodes:
        i = index[u]
        for v, w in g.out_neighbors(u).items():
            if v != u:
                adj[i, index[v]] = 1.0
                wts[i, index[v]] = w
    if g.directed:
        sym = adj + adj.T
    else:
        sym = adj

    if weighted and wts.any():
        max_w = wts.max()
        cw = np.cbrt(wts / max_w)
        s = cw + cw.T if g.directed else cw
    else:
        s = sym
    closed = ((s @ s) * s.T).sum(axis=1)            # diagonal of S^3 without forming S^3
    tri_count = ((sym @ sym) * sym.T).sum(axis=1)   # unweighted version, for the triangle count

    if g.directed:
        d_tot = adj.sum(axis=0) + adj.sum(axis=1)
        d_recip = (adj * adj.T).sum(axis=1)
        denom = 2.0 * (d_tot * (d_tot - 1) - 2.0 * d_recip)
        triangles = tri_count / 2.0       # each directed triangle is counted twice in (S^3)_uu
        degree = d_tot
    else:
        degree = adj.sum(axis=1)
        denom = degree * (degree - 1)
        triangles = tri_count / 2.0
    with np.errstate(divide="ignore", invalid="ignore"):
        coef = np.where(denom > 0, closed / np.where(denom > 0, denom, 1.0), 0.0)
    return nodes, coef, degree, triangles


def _fit(out, items):
    """Drop entries from the end of `items` (a list inside `out`) until the output fits in 8 KB."""
    while items and len(json.dumps(out).encode("utf-8")) > _SIZE_BUDGET:
        items.pop()
    return len(items)


def run(store, graph_id, node=None, top_k=10, weighted=False, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. clustering_coefficient takes "
                     f"graph_id, node, top_k and weighted.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if not isinstance(weighted, bool):
        return error(f"weighted must be true or false; got {weighted!r}.")
    if node is not None:
        err = check_node(g, node)
        if err:
            return err
    if g.number_of_nodes() == 0:
        return error(f"Graph '{graph_id}' has no nodes, so it has no clustering coefficient. "
                     f"Use list_graphs to pick another graph.")

    nodes, coef, degree, triangles = _clustering(g, weighted)
    average = round(float(coef.mean()), 6)
    kind = ("weighted " if weighted else "") + ("directed " if g.directed else "")
    tri_key = "directed_triangles" if g.directed else "triangles"
    note = "" if not weighted or g.weighted else f" '{graph_id}' is unweighted, so weighted=true changes nothing."

    if node is not None:
        i = nodes.index(node)
        c = round(float(coef[i]), 6)
        entry = node_ref(g, node, clustering=c, degree=int(degree[i]), **{tri_key: int(round(triangles[i]))})
        result = {"node": entry, "average_clustering": average, "directed": g.directed, "weighted": weighted}
        if degree[i] < 2:
            meaning = "because it has fewer than two neighbours, so no triangle is possible"
        elif weighted:
            meaning = "(the weight-scaled share of closed triangles around it)"
        else:
            meaning = f"meaning {c:.0%} of the possible links among its neighbours exist"
        summary = (f"{entry['label']} ({node}) has {kind}clustering coefficient {c}, {meaning}. "
                   f"The average clustering of '{graph_id}' is {average}.{note}")
        return ok(result, summary)

    ranked = sorted(((round(float(c), 6), n, i) for i, (n, c) in enumerate(zip(nodes, coef))),
                    key=lambda t: (-t[0], t[1]))[:k]
    top = [node_ref(g, n, clustering=c, degree=int(degree[i])) for c, n, i in ranked]
    result = {"average_clustering": average, "nodes": len(nodes),
              "nodes_with_zero_clustering": int((coef == 0).sum()),
              "directed": g.directed, "weighted": weighted, "top": top}
    shown = _fit(result, top)
    best = top[0]
    summary = (f"The average {kind}clustering coefficient of '{graph_id}' is {average} over {len(nodes)} nodes; "
               f"the highest is {best['label']} ({best['id']}) with {best['clustering']}. "
               f"Showing the top {shown} nodes.{note}")
    return ok(result, summary)
