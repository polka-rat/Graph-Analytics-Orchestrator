"""pagerank: PageRank by power iteration, top-k.

A node's PageRank is the stationary share of a random surfer that follows links
with probability `damping` and otherwise jumps to a random node. Nodes reached
by many or strong links score higher. The iteration stops when the L1 change
drops below n * 1e-12, which is far tighter than the 6-decimal output, so the
rounded scores match the exact fixed point.

Rules (the validator checks them):
- Implement the algorithm yourself: standard library, NumPy and graphkit only.
- Get graphs only from the store; never open files, print, or use the network.
- Never crash: return error("what went wrong and how to fix it") instead.
- Return every node as node_ref(g, node, ...), so it has both an id and a label.
- Keep the output under 8 KB: respect top_k.
- Be deterministic: same input, same output.
"""
import numpy as np

from graphkit.contract import check_top_k, error, get_graph, node_ref, ok

DEFAULT_DAMPING = 0.85
TOLERANCE = 1e-12
MAX_ITERATIONS = 1000


def run(store, graph_id, damping=DEFAULT_DAMPING, top_k=10, **params) -> dict:
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     "pagerank takes graph_id, damping and top_k.")
    if isinstance(damping, bool) or not isinstance(damping, (int, float)) \
            or not 0.0 <= float(damping) <= 1.0:
        return error(f"damping must be a number between 0 and 1; got {damping!r}.")
    damping = float(damping)
    k, err = check_top_k(top_k)
    if err:
        return err

    nodes = g.nodes()
    n = len(nodes)
    if n == 0:
        return error(f"Graph '{graph_id}' has no nodes, so PageRank is undefined.")

    index = {node: i for i, node in enumerate(nodes)}
    sources, targets, weights = [], [], []
    for u in nodes:
        for v, w in g.out_neighbors(u).items():
            sources.append(index[u])
            targets.append(index[v])
            weights.append(w)
    if weights and min(weights) <= 0.0:
        return error("All edge weights must be positive for PageRank; "
                     "this graph has a non-positive weight.")

    src = np.array(sources, dtype=np.intp)
    dst = np.array(targets, dtype=np.intp)
    w = np.array(weights, dtype=np.float64)
    out_weight = np.bincount(src, weights=w, minlength=n)
    dangling = out_weight == 0.0

    # Power iteration: follow edges proportionally to their weight, spread the
    # rank of dangling nodes uniformly, and add the teleport probability.
    rank = np.full(n, 1.0 / n)
    for _ in range(MAX_ITERATIONS):
        dangling_sum = rank[dangling].sum()
        base = (1.0 - damping) / n + damping * dangling_sum / n
        new_rank = np.full(n, base)
        if len(src):
            flow = damping * rank[src] * w / out_weight[src]
            new_rank += np.bincount(dst, weights=flow, minlength=n)
        delta = float(np.abs(new_rank - rank).sum())
        rank = new_rank
        if delta < n * TOLERANCE:
            break
    else:
        return error(f"PageRank did not converge within {MAX_ITERATIONS} iterations; "
                     "try a smaller damping value.")

    scores = {node: round(float(rank[index[node]]), 6) for node in nodes}
    top = sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:k]
    result = [node_ref(g, node, score=score) for node, score in top]
    best = result[0]
    summary = (f"{best['label']} ranks first of {n} nodes with PageRank {best['score']} "
               f"(damping {damping}).")
    return ok(result, summary)
