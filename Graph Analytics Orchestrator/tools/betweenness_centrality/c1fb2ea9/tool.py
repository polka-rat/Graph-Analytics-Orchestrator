"""Computes betweenness centrality for all nodes in a graph using Brandes' algorithm.

Rules (the validator checks them):
- Implement the algorithm yourself: standard library, NumPy and graphkit only.
- Get graphs only from the store; never open files, print, or use the network.
- Never crash: return error("what went wrong and how to fix it") instead.
- Return every node as node_ref(g, node, ...), so it has both an id and a label.
- Keep the output under 8 KB: respect top_k.
- Be deterministic: same input, same output.
"""
from __future__ import annotations

from collections import deque
from typing import Any

from graphkit.contract import check_top_k, error, get_graph, node_ref, ok


def _brandes_betweenness(g, normalized: bool = True) -> dict[str, float]:
    """Calculates betweenness centrality for all nodes in O(V * (V + E)) time using Brandes' algorithm."""
    nodes = g.nodes()
    n = len(nodes)
    cb = {v: 0.0 for v in nodes}

    for s in nodes:
        # Step 1: Single-source shortest paths via BFS
        stack: list[str] = []
        pred: dict[str, list[str]] = {w: [] for w in nodes}
        sigma: dict[str, int] = {w: 0 for w in nodes}
        sigma[s] = 1
        dist: dict[str, int] = {w: -1 for w in nodes}
        dist[s] = 0
        queue: deque[str] = deque([s])

        while queue:
            v = queue.popleft()
            stack.append(v)
            nbrs = g.out_neighbors(v) if g.directed else g.neighbors(v)
            for w in nbrs:
                # Node w found for the first time?
                if dist[w] < 0:
                    dist[w] = dist[v] + 1
                    queue.append(w)
                # Shortest path to w via v?
                if dist[w] == dist[v] + 1:
                    sigma[w] += sigma[v]
                    pred[w].append(v)

        # Step 2: Accumulation of dependencies (back-propagation from leaves)
        delta: dict[str, float] = {w: 0.0 for w in nodes}
        while stack:
            w = stack.pop()
            for v in pred[w]:
                delta[v] += (sigma[v] / sigma[w]) * (1.0 + delta[w])
            if w != s:
                cb[w] += delta[w]

    # In undirected graphs, every pair (s, t) is traversed twice (s->t and t->s)
    if not g.directed:
        for v in nodes:
            cb[v] /= 2.0

    # Normalization: divide by the number of possible node pairs excluding v
    if normalized:
        if n > 2:
            scale = 1.0 / ((n - 1) * (n - 2)) if g.directed else 2.0 / ((n - 1) * (n - 2))
            for v in nodes:
                cb[v] *= scale
        else:
            for v in nodes:
                cb[v] = 0.0

    return cb


def run(store, graph_id: str, top_k: int = 10, normalized: bool = True, **params) -> dict:
    g, err = get_graph(store, graph_id)
    if err:
        return err

    if params:
        return error(
            f"Unknown parameter(s): {', '.join(params)}. "
            f"betweenness_centrality takes graph_id, top_k, and normalized."
        )

    k, err = check_top_k(top_k)
    if err:
        return err

    if not isinstance(normalized, bool):
        return error("normalized must be a boolean (true or false).")

    n_nodes = g.number_of_nodes()
    if n_nodes == 0:
        return ok([], f"Graph '{graph_id}' has 0 nodes.")

    scores = _brandes_betweenness(g, normalized=normalized)

    # Sort descending by score; break ties deterministically by node ID in ascending order
    top = sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:k]
    result = [node_ref(g, n, score=round(s, 6)) for n, s in top]

    best = result[0]
    summary = (
        f"{best['label']} ({best['id']}) has the highest betweenness centrality "
        f"({best['score']}) among {n_nodes} nodes."
    )
    return ok(result, summary)
