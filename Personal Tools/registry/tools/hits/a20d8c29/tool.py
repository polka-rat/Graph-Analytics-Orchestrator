"""hits: Kleinberg's HITS hub and authority scores, by power iteration.

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

from graphkit.contract import (
    MAX_OUTPUT_BYTES,
    check_top_k,
    error,
    get_graph,
    node_ref,
    ok,
)

RANK_FIELDS = ("authority", "hub")


def run(store, graph_id, top_k=10, max_iter=100, tol=1e-8, rank_by="authority",
        use_weights=True, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(
            f"Unknown parameter(s): {', '.join(sorted(params))}. hits takes graph_id, top_k, "
            f"max_iter, tol, rank_by and use_weights."
        )
    k, err = check_top_k(top_k)
    if err:
        return err
    if isinstance(max_iter, bool) or not isinstance(max_iter, int) or not 1 <= max_iter <= 10000:
        return error(f"max_iter must be a whole number from 1 to 10000; got {max_iter!r}.")
    if isinstance(tol, bool) or not isinstance(tol, (int, float)) or not 0 < tol < 1:
        return error(f"tol must be a number greater than 0 and less than 1; got {tol!r}.")
    if rank_by not in RANK_FIELDS:
        return error(f"rank_by must be one of {' or '.join(RANK_FIELDS)}; got {rank_by!r}.")
    if not isinstance(use_weights, bool):
        return error(f"use_weights must be true or false; got {use_weights!r}.")

    n = g.number_of_nodes()
    if n == 0:
        return error(f"Graph '{g.graph_id}' has no nodes, so HITS has nothing to score.")
    if g.number_of_edges() == 0:
        return error(
            f"Graph '{g.graph_id}' has no edges. HITS scores nodes by who links to whom, "
            f"so it needs at least one edge. Use graph_summary to inspect the graph."
        )

    # Adjacency matrix in the graph's own node order. A[i, j] is the weight of edge i -> j;
    # an undirected edge fills both A[i, j] and A[j, i].
    nodes = g.nodes()
    index = {v: i for i, v in enumerate(nodes)}
    adjacency = np.zeros((n, n), dtype=float)
    for u, v, w in g.edges():
        value = float(w) if use_weights else 1.0
        adjacency[index[u], index[v]] = value
        if not g.directed:
            adjacency[index[v], index[u]] = value

    # Power iteration on the mutually recursive definition
    #     authority(v) = sum of hub(u) over every edge u -> v        (a = h @ A)
    #     hub(u)       = sum of authority(v) over every edge u -> v  (h = A @ a)
    # which converges to the principal eigenvectors of A^T A and A A^T. Hub values are
    # rescaled by their maximum each round to stop them growing without bound.
    hub = np.full(n, 1.0 / n)
    authority = hub @ adjacency
    converged = False
    iterations = 0
    for _ in range(max_iter):
        iterations += 1
        previous = hub
        authority = hub @ adjacency
        hub = adjacency @ authority
        largest = hub.max()
        if not np.isfinite(largest) or largest <= 0:
            return error(
                f"HITS did not produce usable scores on '{g.graph_id}': the hub values "
                f"collapsed to zero. This happens on graphs with no reciprocated structure; "
                f"try a different graph or use degree_centrality instead."
            )
        hub = hub / largest
        if np.abs(hub - previous).sum() < tol:
            converged = True
            break

    if not converged:
        return error(
            f"HITS did not converge on '{g.graph_id}' within {max_iter} iterations "
            f"(tolerance {tol}). Raise max_iter or raise tol and try again."
        )

    # Final scores are normalised so that each vector sums to 1.
    hub_total, authority_total = hub.sum(), authority.sum()
    if hub_total <= 0 or authority_total <= 0:
        return error(
            f"HITS produced an all-zero score vector on '{g.graph_id}', so the nodes cannot "
            f"be ranked. Use graph_summary to check that the graph has edges."
        )
    hub = hub / hub_total
    authority = authority / authority_total

    scores = {
        v: (round(float(authority[i]), 6), round(float(hub[i]), 6))
        for v, i in index.items()
    }
    # Rank by the requested score, breaking ties by node id ascending for determinism.
    position = 0 if rank_by == "authority" else 1
    ranked = sorted(nodes, key=lambda v: (-scores[v][position], v))[:k]
    result = [
        node_ref(g, v, authority=scores[v][0], hub=scores[v][1])
        for v in ranked
    ]

    def build(entries, truncated):
        best = entries[0]
        other = "hub" if rank_by == "authority" else "authority"
        summary = (
            f"{best['label']} has the highest {rank_by} score ({best[rank_by]}) of the "
            f"{n:,} nodes in '{g.graph_id}'; its {other} score is {best[other]}. "
            f"Converged in {iterations} iterations."
        )
        if not g.directed:
            summary += " The graph is undirected, so hub and authority scores are identical."
        if truncated:
            summary += (
                f" Showing the top {len(entries)} of the {k} requested, to stay within the "
                f"8 KB response limit; ask for a smaller top_k to avoid this."
            )
        return ok(entries, summary)

    # Honour top_k, but never exceed the hard 8 KB response limit: long node labels mean
    # that 100 entries can overflow it, so drop the lowest-ranked entries until it fits.
    out = build(result, False)
    while len(result) > 1 and len(json.dumps(out, allow_nan=False, sort_keys=True).encode("utf-8")) > MAX_OUTPUT_BYTES:
        result = result[:-1]
        out = build(result, True)
    return out
