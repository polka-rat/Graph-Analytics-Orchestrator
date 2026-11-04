"""pagerank: PageRank by power iteration (NumPy), top-k nodes.

score = (1 - damping) / n + damping * (rank flowing in along edges + rank of dangling nodes / n)

Each node splits its rank over its out-edges in proportion to the edge weights (equally when
unweighted). Nodes with no out-edges ("dangling") spread their rank evenly over all nodes, which is
the NetworkX convention. Undirected edges work in both directions. Cost: O(iterations * E).
"""
import json

import numpy as np

from graphkit.contract import check_top_k, error, get_graph, node_ref, ok

TOLERANCE = 1e-12  # stop when the total change in one iteration is below this
MAX_ITERATIONS = 1000
SIZE_BUDGET = 8000  # bytes of JSON; the contract limit is 8 KB (8192)


def _edge_arrays(g, index, use_weights):
    src, dst, wts = [], [], []
    for u, v, w in g.edges():
        w = w if use_weights else 1.0
        src.append(index[u])
        dst.append(index[v])
        wts.append(w)
        if not g.directed and u != v:
            src.append(index[v])
            dst.append(index[u])
            wts.append(w)
    return np.array(src, dtype=np.int64), np.array(dst, dtype=np.int64), np.array(wts, dtype=float)


def run(store, graph_id, damping=0.85, top_k=10, weighted=True, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. pagerank takes graph_id, damping, "
                     f"top_k and weighted.")
    if isinstance(damping, bool) or not isinstance(damping, (int, float)) or not 0 <= damping < 1:
        return error(f"damping must be a number from 0 up to (but not including) 1; got {damping!r}. "
                     f"The usual value is 0.85.")
    if not isinstance(weighted, bool):
        return error(f"weighted must be true or false; got {weighted!r}.")
    k, err = check_top_k(top_k)
    if err:
        return err
    nodes = g.nodes()
    n = len(nodes)
    if n == 0:
        return error(f"Graph '{graph_id}' has no nodes, so PageRank is undefined.")

    use_weights = weighted and g.weighted
    index = {node: i for i, node in enumerate(nodes)}
    src, dst, wts = _edge_arrays(g, index, use_weights)
    if wts.size and wts.min() < 0:
        return error(f"Graph '{graph_id}' has negative edge weights, which PageRank cannot use. "
                     f"Call it again with weighted=false.")

    out_strength = np.bincount(src, weights=wts, minlength=n)
    dangling = out_strength == 0
    share = np.divide(wts, out_strength[src], out=np.zeros_like(wts), where=out_strength[src] > 0)

    rank = np.full(n, 1.0 / n)
    iterations = 0
    for iterations in range(1, MAX_ITERATIONS + 1):
        inflow = np.bincount(dst, weights=rank[src] * share, minlength=n)
        new_rank = (1 - damping) / n + damping * (inflow + rank[dangling].sum() / n)
        change = np.abs(new_rank - rank).sum()
        rank = new_rank
        if change < TOLERANCE:
            break
    else:
        return error(f"PageRank did not converge within {MAX_ITERATIONS} iterations on '{graph_id}'. "
                     f"Try a smaller damping value.")
    rank = rank / rank.sum()

    # tie-break on id so equal scores (e.g. symmetric nodes) come out in a fixed order
    order = sorted(range(n), key=lambda i: (-round(float(rank[i]), 10), nodes[i]))[:k]
    result = [node_ref(g, nodes[i], rank=position, score=round(float(rank[i]), 8))
              for position, i in enumerate(order, 1)]
    how = "weighted by edge weight" if use_weights else "ignoring edge weights"
    best = result[0]
    summary = (f"{best['label']} is the highest-ranked of {n:,} nodes by PageRank "
               f"(score {best['score']}, damping {damping:g}, {how}; converged in {iterations} iterations).")
    out = ok(result, summary)
    # long labels can push top_k=100 past the 8 KB limit: drop the lowest-ranked entries until it fits
    while len(result) > 1 and len(json.dumps(out)) > SIZE_BUDGET:
        result = result[:-1]
        out = ok(result, f"{summary} Only the top {len(result)} are shown to stay under the 8 KB output limit.")
    return out
