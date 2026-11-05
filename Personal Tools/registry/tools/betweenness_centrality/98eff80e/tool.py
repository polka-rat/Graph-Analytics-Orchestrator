"""Betweenness centrality tool using Ulrik Brandes' algorithm.

Computes exact shortest-path betweenness centrality for all nodes in
directed or undirected, unweighted or weighted graphs.
"""
from __future__ import annotations

import json
from collections import deque
from heapq import heappop, heappush
from itertools import count

from graphkit.contract import check_top_k, error, get_graph, node_ref, ok


def _brandes_betweenness(
    nodes: list[str],
    adj_out: dict[str, tuple],
    directed: bool,
    weighted: bool,
    normalized: bool,
    endpoints: bool,
) -> dict[str, float]:
    """Pure Python implementation of Brandes' betweenness centrality matching NetworkX."""
    n = len(nodes)
    betweenness = {v: 0.0 for v in nodes}
    if n < 2:
        return betweenness

    if weighted:
        c = count()
        for s in nodes:
            S = []
            P: dict[str, list[str]] = {v: [] for v in nodes}
            sigma = {v: 0.0 for v in nodes}
            D: dict[str, float] = {}
            sigma[s] = 1.0
            seen: dict[str, float] = {s: 0.0}
            Q = [(0.0, next(c), s, s)]
            while Q:
                dist, _, pred, v = heappop(Q)
                if v in D:
                    continue
                sigma[v] += sigma[pred]
                S.append(v)
                D[v] = dist
                for w, weight in adj_out[v]:
                    vw_dist = dist + weight
                    if w not in D and (w not in seen or vw_dist < seen[w]):
                        seen[w] = vw_dist
                        heappush(Q, (vw_dist, next(c), v, w))
                        sigma[w] = 0.0
                        P[w] = [v]
                    elif vw_dist == seen[w]:
                        sigma[w] += sigma[v]
                        P[w].append(v)

            delta = {v: 0.0 for v in S}
            if endpoints:
                betweenness[s] += len(S) - 1
                while S:
                    w = S.pop()
                    coeff = (1.0 + delta[w]) / sigma[w]
                    for v in P[w]:
                        delta[v] += sigma[v] * coeff
                    if w != s:
                        betweenness[w] += delta[w] + 1.0
            else:
                while S:
                    w = S.pop()
                    coeff = (1.0 + delta[w]) / sigma[w]
                    for v in P[w]:
                        delta[v] += sigma[v] * coeff
                    if w != s:
                        betweenness[w] += delta[w]
    else:
        for s in nodes:
            S = []
            P = {v: [] for v in nodes}
            sigma = {v: 0.0 for v in nodes}
            D: dict[str, int] = {s: 0}
            sigma[s] = 1.0
            Q = deque([s])
            while Q:
                v = Q.popleft()
                S.append(v)
                Dv = D[v]
                sigmav = sigma[v]
                for w in adj_out[v]:
                    if w not in D:
                        Q.append(w)
                        D[w] = Dv + 1
                    if D[w] == Dv + 1:
                        sigma[w] += sigmav
                        P[w].append(v)

            delta = {v: 0.0 for v in S}
            if endpoints:
                betweenness[s] += len(S) - 1
                while S:
                    w = S.pop()
                    coeff = (1.0 + delta[w]) / sigma[w]
                    for v in P[w]:
                        delta[v] += sigma[v] * coeff
                    if w != s:
                        betweenness[w] += delta[w] + 1.0
            else:
                while S:
                    w = S.pop()
                    coeff = (1.0 + delta[w]) / sigma[w]
                    for v in P[w]:
                        delta[v] += sigma[v] * coeff
                    if w != s:
                        betweenness[w] += delta[w]

    # Rescale factor matching NetworkX _rescale
    N = n if endpoints else n - 1
    if N >= 2:
        if normalized:
            scale = 1.0 / (N * (N - 1))
        else:
            scale = 1.0 if directed else 0.5
        if scale != 1.0:
            for v in betweenness:
                betweenness[v] *= scale

    return betweenness


def run(
    store,
    graph_id: str,
    top_k: int = 10,
    normalized: bool = True,
    weighted: bool = False,
    endpoints: bool = False,
    **params,
) -> dict:
    """Compute betweenness centrality for nodes in the given graph."""
    g, err = get_graph(store, graph_id)
    if err:
        return err

    if params:
        return error(f"Unknown parameter(s): {', '.join(sorted(params))}. Supported parameters are top_k, normalized, weighted, endpoints.")

    k, err = check_top_k(top_k)
    if err:
        return err

    if not isinstance(normalized, bool):
        return error(f"normalized must be a boolean (true or false); got {normalized!r}.")

    if not isinstance(weighted, bool):
        return error(f"weighted must be a boolean (true or false); got {weighted!r}.")

    if not isinstance(endpoints, bool):
        return error(f"endpoints must be a boolean (true or false); got {endpoints!r}.")

    nodes = g.nodes()
    if not nodes:
        return ok([], f"Graph '{graph_id}' has 0 nodes.")

    if weighted:
        # Check that all edge weights are strictly positive
        for u, v, w in g.edges():
            if w <= 0.0:
                return error(
                    f"Graph '{graph_id}' contains edge ({u}, {v}) with non-positive weight {w}. "
                    f"Edge weights must be strictly positive (> 0) for weighted shortest paths."
                )
        adj_out = {u: tuple(g.out_neighbors(u).items()) for u in nodes}
    else:
        adj_out = {u: tuple(g.out_neighbors(u).keys()) for u in nodes}

    betweenness = _brandes_betweenness(
        nodes=nodes,
        adj_out=adj_out,
        directed=g.directed,
        weighted=weighted,
        normalized=normalized,
        endpoints=endpoints,
    )

    # Sort deterministically: descending score, ascending node_id for tie-breaking
    top = sorted(betweenness.items(), key=lambda item: (-round(item[1], 6), item[0]))[:k]
    result = [node_ref(g, n, score=round(float(s), 6)) for n, s in top]

    best = result[0]
    summary = (
        f"Computed betweenness centrality for {len(nodes)} nodes in '{graph_id}'. "
        f"{best['label']} ({best['id']}) has the highest score ({best['score']})."
    )

    # Output size safeguard (must not exceed 8192 bytes)
    while len(result) > 1 and len(json.dumps(ok(result, summary), allow_nan=False).encode("utf-8")) > 8192:
        result.pop()

    return ok(result, summary)
