"""link_prediction: rank node pairs that are not yet connected by how likely they are to link.

Neighbourhood-based scores (common neighbours, Jaccard, Adamic-Adar, resource allocation,
preferential attachment) computed for all pairs at once with NumPy matrix products.
Edge direction and weights are ignored: a pair is "connected" if an edge exists in either direction.
"""
import json

import numpy as np

from graphkit.contract import MAX_OUTPUT_BYTES, check_top_k, error, get_graph, node_ref, ok

METHODS = ("adamic_adar", "common_neighbors", "jaccard", "resource_allocation", "preferential_attachment")
MAX_NODES = 3000
SAFE_BYTES = MAX_OUTPUT_BYTES - 1024  # leave room for the envelope


def _scores(method, A, deg):
    """Matrix of scores for every pair (i, j)."""
    if method == "common_neighbors":
        return A @ A
    if method == "jaccard":
        cn = A @ A
        union = deg[:, None] + deg[None, :] - cn
        return np.divide(cn, union, out=np.zeros_like(cn), where=union > 0)
    if method == "adamic_adar":
        w = np.zeros_like(deg)
        mask = deg > 1
        w[mask] = 1.0 / np.log(deg[mask])
        return (A * w[None, :]) @ A
    if method == "resource_allocation":
        w = np.zeros_like(deg)
        mask = deg > 0
        w[mask] = 1.0 / deg[mask]
        return (A * w[None, :]) @ A
    return np.outer(deg, deg)  # preferential_attachment


def run(store, graph_id, method="adamic_adar", node=None, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. link_prediction takes graph_id, method, "
                     f"node and top_k.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if method not in METHODS:
        return error(f"method must be one of {', '.join(METHODS)}; got {method!r}.")

    nodes = g.nodes()
    n = len(nodes)
    if n < 3:
        return error(f"Graph '{graph_id}' has only {n} nodes; link prediction needs at least 3.")
    if n > MAX_NODES:
        return error(f"Graph '{graph_id}' has {n} nodes; this tool handles at most {MAX_NODES}. "
                     f"Use filter_nodes to build a smaller subgraph first.")
    idx = {v: i for i, v in enumerate(nodes)}
    if node is not None:
        if not isinstance(node, str) or node not in idx:
            return error(f"Node '{node}' (parameter 'node') is not in graph '{graph_id}'. "
                         f"Use lookup_node to find node ids.")

    # Symmetric 0/1 adjacency matrix (direction and weights ignored, self-loops dropped).
    A = np.zeros((n, n), dtype=float)
    for u in nodes:
        i = idx[u]
        for v in g.undirected_neighbors(u):
            if v != u:
                A[i, idx[v]] = 1.0
    deg = A.sum(axis=1)

    S = np.round(_scores(method, A, deg), 6)
    candidate = (A == 0)
    np.fill_diagonal(candidate, False)
    if node is None:
        candidate &= np.triu(np.ones((n, n), dtype=bool), k=1)
    else:
        only_row = np.zeros((n, n), dtype=bool)
        only_row[idx[node], :] = True
        candidate &= only_row
    candidate &= S > 0
    rows, cols = np.nonzero(candidate)
    total = len(rows)
    if total == 0:
        where = f" for '{node}'" if node else ""
        return ok([], f"No candidate pairs{where} have a positive {method} score in '{graph_id}'.")

    vals = S[rows, cols]
    if total > k:  # keep everything tied with the k-th best score, then sort exactly
        threshold = np.partition(vals, total - k)[total - k]
        keep = vals >= threshold
        rows, cols, vals = rows[keep], cols[keep], vals[keep]
    pairs = []
    for i, j, s in zip(rows.tolist(), cols.tolist(), vals.tolist()):
        a, b = nodes[i], nodes[j]
        if node is None and b < a:
            a, b = b, a
        pairs.append((-s, a, b))
    pairs.sort()
    pairs = pairs[:k]

    result = [{"source": node_ref(g, a), "target": node_ref(g, b), "score": round(-s, 6)}
              for s, a, b in pairs]
    trimmed = False
    while len(result) > 1 and len(json.dumps(result)) > SAFE_BYTES:
        result.pop()
        trimmed = True

    first = result[0]
    summary = (f"Most likely missing link by {method}: {first['source']['label']} ({first['source']['id']}) and "
               f"{first['target']['label']} ({first['target']['id']}), score {first['score']}. "
               f"Returning {len(result)} of {total:,} unconnected pairs with a positive score"
               f"{' (shortened to fit the output size limit)' if trimmed else ''}.")
    return ok(result, summary)
