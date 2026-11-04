"""Computes Kleinberg's HITS hub and authority centrality scores using power iteration.

Rules:
- Standard library, NumPy, and graphkit only.
- Get graphs only from the store; never open files, print, or use the network.
- Never crash: return error("what went wrong and how to fix it") instead.
- Return every node as node_ref(g, node, ...), so it has both an id and a label.
- Keep the output under 8 KB: respect top_k.
- Deterministic: same input, same output.
"""
from __future__ import annotations

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


def run(
    store,
    graph_id: str,
    top_k: int = 10,
    score_type: str = "hub",
    max_iter: int = 100,
    tol: float = 1e-8,
    normalized: bool = True,
    weighted: bool = True,
    **params,
) -> dict:
    """Computes HITS hub and authority centrality scores for all nodes in the graph."""
    g, err = get_graph(store, graph_id)
    if err:
        return err

    if params:
        unknown = ", ".join(sorted(repr(p) for p in params))
        return error(f"Unknown parameter(s): {unknown}. Use only supported parameters.")

    k, err = check_top_k(top_k)
    if err:
        return err

    if not isinstance(score_type, str) or score_type not in ("hub", "authority"):
        return error("score_type must be either 'hub' or 'authority'.")

    if isinstance(max_iter, bool) or not isinstance(max_iter, int) or max_iter < 1:
        return error(f"max_iter must be a positive integer; got {max_iter!r}.")

    if isinstance(tol, bool) or not isinstance(tol, (int, float)) or tol <= 0:
        return error(f"tol must be a positive number; got {tol!r}.")

    if not isinstance(normalized, bool):
        return error(f"normalized must be a boolean (True or False); got {normalized!r}.")

    if not isinstance(weighted, bool):
        return error(f"weighted must be a boolean (True or False); got {weighted!r}.")

    nodelist = g.nodes()
    n_nodes = len(nodelist)
    if n_nodes == 0:
        return ok([], f"Graph '{graph_id}' contains no nodes.")

    # Edgeless graph edge case
    if g.number_of_edges() == 0:
        items = [(n, 0.0, 0.0, 0.0) for n in nodelist]
        items.sort(key=lambda item: (-round(item[1], 6), item[0]))
        top = items[:k]
        result = [
            node_ref(
                g,
                n,
                score=0.0,
                hub_score=0.0,
                authority_score=0.0,
            )
            for n, _, _, _ in top
        ]
        summary = f"Graph '{graph_id}' has 0 edges; all nodes have hub and authority score 0.0."
        return ok(result, summary)

    # Build adjacency matrix A of shape (N, N)
    node_to_idx = {n: i for i, n in enumerate(nodelist)}
    A = np.zeros((n_nodes, n_nodes), dtype=np.float64)
    for u in nodelist:
        i = node_to_idx[u]
        for v, w in g.out_neighbors(u).items():
            A[i, node_to_idx[v]] = float(w) if weighted else 1.0

    # Power iteration matching NetworkX _hits_power_iteration
    h = np.full(n_nodes, 1.0 / n_nodes, dtype=np.float64)
    a = np.zeros(n_nodes, dtype=np.float64)
    converged = False

    for _ in range(max_iter):
        hlast = h
        a = h @ A
        h = A @ a
        h_max = float(h.max())
        if h_max == 0.0:
            converged = True
            break
        h = h / h_max
        if float(np.abs(h - hlast).sum()) < tol:
            converged = True
            break

    if not converged:
        return error(
            f"HITS power iteration did not converge within {max_iter} iterations (tol={tol}). "
            f"Try increasing max_iter or relaxing tol."
        )

    # Post-iteration scaling / normalization
    if normalized:
        h_sum = float(h.sum())
        if h_sum > 0.0:
            h = h / h_sum
        a_sum = float(a.sum())
        if a_sum > 0.0:
            a = a / a_sum
    else:
        a_max = float(a.max())
        if a_max > 0.0:
            a = a / a_max

    # Rank nodes deterministically by (-round(primary_score, 6), node_id)
    items = []
    for i, n in enumerate(nodelist):
        hub_s = float(h[i])
        auth_s = float(a[i])
        primary_s = hub_s if score_type == "hub" else auth_s
        items.append((n, primary_s, hub_s, auth_s))

    items.sort(key=lambda item: (-round(item[1], 6), item[0]))
    top = items[:k]

    # Format result entries
    result = [
        node_ref(
            g,
            n,
            score=round(primary_s, 6),
            hub_score=round(hub_s, 6),
            authority_score=round(auth_s, 6),
        )
        for n, primary_s, hub_s, auth_s in top
    ]

    best = top[0]
    summary = (
        f"{g.label(best[0])} ({best[0]}) is the top {score_type} "
        f"with score {round(best[1], 6)} "
        f"(hub: {round(best[2], 6)}, authority: {round(best[3], 6)}) "
        f"in '{graph_id}'."
    )

    out = ok(result, summary)

    # Ensure output strictly stays within MAX_OUTPUT_BYTES (8192 bytes)
    text = json.dumps(out, allow_nan=False)
    if len(text.encode("utf-8")) > MAX_OUTPUT_BYTES:
        # Fallback 1: Retain primary score and use compact summary
        result = [
            node_ref(g, n, score=round(primary_s, 6))
            for n, primary_s, _, _ in top
        ]
        summary = f"Top {len(result)} {score_type}s in '{graph_id}'."
        out = ok(result, summary)
        text = json.dumps(out, allow_nan=False)

        # Fallback 2: Prune entries if still above limit
        while len(text.encode("utf-8")) > MAX_OUTPUT_BYTES and len(result) > 1:
            result.pop()
            summary = f"Top {len(result)} {score_type}s in '{graph_id}'."
            out = ok(result, summary)
            text = json.dumps(out, allow_nan=False)

    return out
