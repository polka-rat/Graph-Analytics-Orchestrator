"""Calculates a topological ordering of a directed acyclic graph (DAG), or detects a cycle.

Rules (the validator checks them):
- Implement the algorithm yourself: standard library, NumPy and graphkit only.
- Get graphs only from the store; never open files, print, or use the network.
- Never crash: return error("what went wrong and how to fix it") instead.
- Return every node as node_ref(g, node, ...), so it has both an id and a label.
- Keep the output under 8 KB.
- Be deterministic: same input, same output.
"""
from __future__ import annotations

import heapq
from typing import Any

from graphkit.contract import check_top_k, error, get_graph, node_ref, ok


def _find_cycle(g, candidates: set[str]) -> list[str]:
    """Finds a simple directed cycle within candidate nodes using depth-first search."""
    visited: dict[str, int] = {}  # 1 = currently in stack, 2 = fully explored
    path: list[str] = []
    cycle: list[str] = []

    def dfs(u: str) -> bool:
        nonlocal cycle
        visited[u] = 1
        path.append(u)
        for v in sorted(g.out_neighbors(u)):
            if v not in candidates:
                continue
            if visited.get(v) == 1:
                # Back-edge found: cycle detected
                idx = path.index(v)
                cycle = path[idx:] + [v]
                return True
            if v not in visited:
                if dfs(v):
                    return True
        visited[u] = 2
        path.pop()
        return False

    for node in sorted(candidates):
        if node not in visited:
            if dfs(node):
                break
    return cycle


def run(store, graph_id: str, top_k: int | None = None, **params) -> dict:
    g, err = get_graph(store, graph_id)
    if err:
        return err

    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. topological_sort takes graph_id.")

    if top_k is not None:
        k, err = check_top_k(top_k)
        if err:
            return err
    else:
        k = None

    if not g.directed:
        return error(
            f"Graph '{graph_id}' is undirected. Topological sort requires a directed acyclic graph (DAG)."
        )

    n_nodes = g.number_of_nodes()
    if n_nodes == 0:
        return ok([], f"Graph '{graph_id}' has 0 nodes.")

    # Kahn's algorithm with min-heap for deterministic tie-breaking by node ID
    in_degrees = {n: len(g.in_neighbors(n)) for n in g.nodes()}
    zero_in_heap = [n for n, d in in_degrees.items() if d == 0]
    heapq.heapify(zero_in_heap)

    ordering: list[str] = []
    while zero_in_heap:
        u = heapq.heappop(zero_in_heap)
        ordering.append(u)
        for v in g.out_neighbors(u):
            in_degrees[v] -= 1
            if in_degrees[v] == 0:
                heapq.heappush(zero_in_heap, v)

    # Check if a valid topological sort of all nodes was found
    if len(ordering) == n_nodes:
        result_nodes = ordering if k is None else ordering[:k]
        result = [node_ref(g, n) for n in result_nodes]
        summary_preview = " -> ".join(n for n in ordering[:5])
        if len(ordering) > 5:
            summary_preview += f" ... ({n_nodes} courses total)"
        summary = f"Graph '{graph_id}' is a DAG. Found topological ordering: {summary_preview}."
        return ok(result, summary)

    # Graph contains a directed cycle
    remaining = {n for n, d in in_degrees.items() if d > 0}
    cycle = _find_cycle(g, remaining)
    cycle_str = " -> ".join(cycle) if cycle else "detected"
    msg = (
        f"Graph '{graph_id}' is not a DAG; it contains a directed cycle: {cycle_str}. "
        f"Topological sort requires an acyclic graph."
    )
    cycle_refs = [node_ref(g, n) for n in cycle] if cycle else []
    return {
        "status": "error",
        "result": cycle_refs,
        "summary": msg,
        "result_graph_id": None,
        "error": msg,
    }
