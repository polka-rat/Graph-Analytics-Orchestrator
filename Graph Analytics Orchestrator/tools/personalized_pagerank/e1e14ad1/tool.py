"""personalized_pagerank: PageRank that restarts at one source node (random walk with restart).

Power iteration on  pi = d * P^T pi + (1 - d) * e_source.  Dangling nodes (no out-edges) send
their mass back to the source, so scores stay local and always sum to 1.
"""
import json

import numpy as np

from graphkit.contract import check_node, check_top_k, error, get_graph, node_ref, ok

TOL = 1e-10          # stop when the L1 change between iterations is below this
MAX_ITER = 5000      # damping 0.99 needs up to ~2400 iterations on slow-mixing (e.g. bipartite) graphs
SIZE_BUDGET = 7000   # bytes of JSON; the contract limit is 8 KB


def _walk(g, ids, use_weights):
    """Edge arrays (src, dst, p), p = transition probability, plus the mask of dangling nodes."""
    index = {n: i for i, n in enumerate(ids)}
    # out_neighbors already lists both directions for undirected graphs
    edges = [(index[u], index[v], w if use_weights else 1.0)
             for u in ids for v, w in g.out_neighbors(u).items() if w > 0]
    arr = np.array(edges, dtype=float).reshape(-1, 3)
    src, dst, w = arr[:, 0].astype(int), arr[:, 1].astype(int), arr[:, 2]
    out = np.bincount(src, weights=w, minlength=len(ids))
    return src, dst, w / out[src], out == 0


def _iterate(src, dst, p, dangling, r, damping):
    """Returns (scores, iterations, converged)."""
    pi = r.copy()
    for it in range(1, MAX_ITER + 1):
        spread = np.bincount(dst, weights=p * pi[src], minlength=len(pi))
        new = damping * (spread + pi[dangling].sum() * r) + (1 - damping) * r
        change = np.abs(new - pi).sum()
        pi = new
        if change < TOL:
            return pi, it, True
    return pi, MAX_ITER, False


def run(store, graph_id, node=None, damping=0.85, use_weights=False, include_source=False, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. personalized_pagerank takes graph_id, "
                     f"node, damping, use_weights, include_source and top_k.")
    err = check_node(g, node)
    if err:
        return err
    if isinstance(damping, bool) or not isinstance(damping, (int, float)) or not 0 <= damping < 1:
        return error(f"damping must be a number from 0 up to (not including) 1; got {damping!r}. Try 0.85.")
    if not isinstance(use_weights, bool) or not isinstance(include_source, bool):
        return error("use_weights and include_source must be true or false.")
    k, err = check_top_k(top_k)
    if err:
        return err

    ids = g.nodes()
    r = np.zeros(len(ids))
    r[ids.index(node)] = 1.0
    pi, iterations, converged = _iterate(*_walk(g, ids, use_weights), r, damping)

    source_score = float(pi[ids.index(node)])
    scores = [(round(float(s), 6), n) for n, s in zip(ids, pi) if s > 0 and (include_source or n != node)]
    scores.sort(key=lambda item: (-item[0], item[1]))  # ties broken by id
    ranking = [node_ref(g, n, score=s) for s, n in scores[:k]]
    result = {"source": node_ref(g, node), "damping": damping, "weighted": use_weights and g.weighted,
              "source_score": round(source_score, 6), "scored_nodes": len(scores), "iterations": iterations,
              "converged": converged, "ranking": ranking}
    while ranking and len(json.dumps(result)) + 600 > SIZE_BUDGET:
        ranking.pop()  # long labels: list fewer nodes rather than break the 8 KB cap

    name = f"{result['source']['label']} ({node})"
    if not scores:
        summary = f"No other node is reachable from {name}, so it keeps all of its own score ({source_score:.3f})."
    else:
        best = ", ".join(f"{e['label']} ({e['id']}, {e['score']})" for e in ranking[:3])
        more = f" Showing the top {len(ranking)}." if len(scores) > len(ranking) else ""
        left_out = "" if include_source else ", source excluded"
        summary = (f"Most relevant to {name}: {best} (damping {damping}{left_out}). "
                   f"{len(scores)} nodes receive a score.{more}")
    if not converged:
        summary += f" Warning: not fully converged after {MAX_ITER} iterations; try a smaller damping."
    return ok(result, summary)
