"""HITS hub and authority scores by power iteration (Kleinberg's algorithm).

A good authority is pointed to by many good hubs; a good hub points to many good
authorities. With adjacency matrix A (A[i, j] = 1 for an edge i -> j):
    authority = A^T hub,   hub = A authority,
each normalised to sum to 1 after every step, until the change is below tol.
"""
import json

import numpy as np

from graphkit.contract import MAX_OUTPUT_BYTES, check_top_k, error, get_graph, node_ref, ok

SORT_KEYS = ("authority", "hub")


def run(store, graph_id, top_k=10, sort_by="authority", max_iter=1000, tol=1e-10, use_weights=False, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. hits takes graph_id, top_k, sort_by, "
                     f"max_iter, tol and use_weights.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if sort_by not in SORT_KEYS:
        return error(f"sort_by must be 'authority' or 'hub'; got {sort_by!r}.")
    if isinstance(max_iter, bool) or not isinstance(max_iter, int) or not 1 <= max_iter <= 100000:
        return error(f"max_iter must be a whole number from 1 to 100000; got {max_iter!r}.")
    if isinstance(tol, bool) or not isinstance(tol, (int, float)) or not 0 < tol < 1:
        return error(f"tol must be a number between 0 and 1, e.g. 1e-10; got {tol!r}.")
    if not isinstance(use_weights, bool):
        return error(f"use_weights must be true or false; got {use_weights!r}.")
    if g.number_of_edges() == 0:
        return error(f"Graph '{graph_id}' has no edges, so hub and authority scores are undefined. "
                     f"Use list_graphs to pick a graph with edges.")

    nodes = sorted(g.nodes())
    index = {nd: i for i, nd in enumerate(nodes)}
    n = len(nodes)
    A = np.zeros((n, n))
    for u, v, w in g.edges():
        val = w if use_weights else 1.0
        A[index[u], index[v]] = val
        if not g.directed:
            A[index[v], index[u]] = val
    if use_weights and (A < 0).any():
        return error("HITS needs non-negative edge weights; call again with use_weights=false.")

    hub = np.full(n, 1.0 / n)
    converged = False
    for _ in range(max_iter):
        auth = A.T @ hub
        auth /= auth.sum()
        new_hub = A @ auth
        new_hub /= new_hub.sum()
        delta = np.abs(new_hub - hub).sum()
        hub = new_hub
        if delta < tol:
            converged = True
            break
    auth = A.T @ hub
    auth /= auth.sum()

    scores = {nd: (round(float(auth[i]), 6), round(float(hub[i]), 6)) for nd, i in index.items()}
    primary = 0 if sort_by == "authority" else 1
    top = sorted(scores.items(), key=lambda item: (-item[1][primary], item[0]))[:k]
    result = [node_ref(g, nd, authority=a, hub=h) for nd, (a, h) in top]

    best_auth = min(scores, key=lambda nd: (-scores[nd][0], nd))
    best_hub = min(scores, key=lambda nd: (-scores[nd][1], nd))
    summary = (f"Top authority in '{graph_id}' is {g.label(best_auth)} ({scores[best_auth][0]}); "
               f"top hub is {g.label(best_hub)} ({scores[best_hub][1]}). Ranked by {sort_by} over {n} nodes.")
    if not g.directed:
        summary += " The graph is undirected, so hub and authority scores are equal."
    if not converged:
        summary += f" Warning: did not converge in {max_iter} iterations; raise max_iter for exact scores."
    out = ok(result, summary)
    # Long labels can push 100 results past the 8 KB limit: drop the lowest-ranked until it fits.
    while len(result) > 1 and len(json.dumps(out)) > MAX_OUTPUT_BYTES - 200:
        result.pop()
    if len(result) < len(top):
        out["summary"] += f" Only the top {len(result)} are listed to keep the output under 8 KB."
    return out
