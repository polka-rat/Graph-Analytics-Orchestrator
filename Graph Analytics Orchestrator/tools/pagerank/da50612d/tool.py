"""PageRank by power iteration: the top_k most important nodes.

The update is x <- d * (x P + (dangling mass) / N) + (1 - d) / N, where P is the
row-normalised (weighted) adjacency matrix and nodes without out-links spread their score
evenly over all nodes. It stops when the L1 change is below N * tol, the same rule as
networkx.pagerank, so the scores match NetworkX.

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

from graphkit.contract import MAX_OUTPUT_BYTES, check_top_k, error, get_graph, node_ref, ok

# Leave room below the 8 KB limit for the summary and the JSON keys.
_SIZE_BUDGET = MAX_OUTPUT_BYTES - 400


def _is_number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _pagerank(g, damping, weighted, max_iter, tol):
    """Return (nodes, scores, iterations, n_dangling); scores is None if it did not converge."""
    nodes = g.nodes()
    index = {n: i for i, n in enumerate(nodes)}
    n = len(nodes)
    a = np.zeros((n, n))
    for u in nodes:
        i = index[u]
        for v, w in g.out_neighbors(u).items():
            a[i, index[v]] = w if weighted else 1.0
    out_weight = a.sum(axis=1)
    dangling = out_weight == 0
    scale = np.zeros(n)
    scale[~dangling] = 1.0 / out_weight[~dangling]
    p = a * scale[:, None]                 # row-stochastic transition matrix (dangling rows stay 0)

    uniform = np.repeat(1.0 / n, n)
    x = uniform.copy()
    for it in range(1, max_iter + 1):
        last = x
        x = damping * (x @ p + x[dangling].sum() * uniform) + (1 - damping) * uniform
        if np.abs(x - last).sum() < n * tol:
            return nodes, x, it, int(dangling.sum())
    return nodes, None, max_iter, int(dangling.sum())


def _fit(out, items):
    """Drop entries from the end of `items` (a list inside `out`) until the output fits in 8 KB."""
    while items and len(json.dumps(out).encode("utf-8")) > _SIZE_BUDGET:
        items.pop()
    return len(items)


def run(store, graph_id, damping=0.85, top_k=10, weighted=True, max_iter=100, tol=1e-06, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. pagerank takes graph_id, damping, "
                     f"top_k, weighted, max_iter and tol.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if not _is_number(damping) or not 0 < damping < 1:
        return error(f"damping must be a number strictly between 0 and 1 (usually 0.85); got {damping!r}.")
    if not isinstance(weighted, bool):
        return error(f"weighted must be true or false; got {weighted!r}.")
    if isinstance(max_iter, bool) or not isinstance(max_iter, int) or not 1 <= max_iter <= 10000:
        return error(f"max_iter must be a whole number from 1 to 10000; got {max_iter!r}.")
    if not _is_number(tol) or not 0 < tol < 1:
        return error(f"tol must be a small positive number such as 1e-6; got {tol!r}.")
    if g.number_of_nodes() == 0:
        return error(f"Graph '{graph_id}' has no nodes, so PageRank is undefined. Use list_graphs to pick another graph.")
    if weighted and any(w < 0 for _, _, w in g.edges()):
        return error(f"Graph '{graph_id}' has negative edge weights, which PageRank cannot use. "
                     f"Call again with weighted=false.")

    nodes, scores, iterations, n_dangling = _pagerank(g, float(damping), weighted, max_iter, float(tol))
    if scores is None:
        return error(f"PageRank did not converge within {max_iter} iterations (tol {tol}). "
                     f"Call again with a larger max_iter, a larger tol, or a smaller damping.")

    ranked = sorted(((round(float(s), 6), n) for n, s in zip(nodes, scores)), key=lambda t: (-t[0], t[1]))[:k]
    result = [node_ref(g, n, score=s) for s, n in ranked]
    shown = _fit({"status": "ok", "result": result, "summary": "", "result_graph_id": None, "error": None}, result)
    best = result[0]
    how = "weighted by edge weight" if weighted and g.weighted else "with every link counted equally"
    summary = (f"{best['label']} ({best['id']}) has the highest PageRank ({best['score']}) of "
               f"{len(nodes)} nodes in '{graph_id}' (damping {damping}, {how}, converged in {iterations} "
               f"iterations). Showing the top {shown}.")
    if n_dangling:
        summary += f" {n_dangling} nodes have no out-links; their score is spread evenly over all nodes."
    return ok(result, summary)
