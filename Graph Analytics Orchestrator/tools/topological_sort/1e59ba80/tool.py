"""TODO: one line saying what this tool computes.

Rules (the validator checks them):
- Implement the algorithm yourself: standard library, NumPy and graphkit only.
- Get graphs only from the store; never open files, print, or use the network.
- Never crash: return error("what went wrong and how to fix it") instead.
- Return every node as node_ref(g, node, ...), so it has both an id and a label.
- Keep the output under 8 KB: respect top_k.
- Be deterministic: same input, same output. Randomised algorithms take a `seed` parameter (default 0).
"""
import heapq
import json
from collections import deque

from graphkit.contract import MAX_OUTPUT_BYTES, error, get_graph, node_ref, ok

SIZE_BUDGET = MAX_OUTPUT_BYTES - 700

# Kahn's algorithm using min-heap 
def _kahn(g):
    indeg = {n: len(g.in_neighbors(n)) for n in g.nodes()}
    level = {n: 0 for n in g.nodes()}
    heap = [n for n, d in indeg.items() if d == 0]
    heapq.heapify(heap)
    order = []
    while heap:
        u = heapq.heappop(heap)
        order.append(u)
        for v in g.out_neighbors(u):
            level[v] = max(level[v], level[u] + 1)
            indeg[v] -= 1
            if indeg[v] == 0:
                heapq.heappush(heap, v)
    blocked = {n for n, d in indeg.items() if d > 0}
    return order, level, blocked

# Check for cycle 
def _find_cycle(g, blocked):
    seen = set()
    u = min(blocked)
    while u not in seen:
        seen.add(u)
        u = min(v for v in g.in_neighbors(u) if v in blocked)
    start = u
    parent = {start: None}
    queue = deque([start])
    while queue:
        u = queue.popleft()
        for v in sorted(g.out_neighbors(u)):
            if v not in blocked:
                continue
            if v == start:
                path = [u]
                while parent[path[-1]] is not None:
                    path.append(parent[path[-1]])
                return path[::-1]
            if v not in parent:
                parent[v] = u
                queue.append(v)
    return [start]


def _size(obj):
    return len(json.dumps(obj).encode("utf-8"))


def run(store, graph_id, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. topological_sort takes only graph_id.")
    if not g.directed:
        return error(f"Graph '{graph_id}' is undirected, but topological_sort needs a directed graph "
                     f"(ideally acyclic, such as 'courses'). Use list_graphs to pick a directed graph.")
    if g.number_of_nodes() == 0:
        return error(f"Graph '{graph_id}' has no nodes, so there is nothing to order. Use list_graphs to pick "
                     f"another graph.")

    n_nodes = g.number_of_nodes()
    order, level, blocked = _kahn(g)

    if blocked:
        cycle = _find_cycle(g, blocked)
        result = {"is_dag": False,
                  "cycle_length": len(cycle),
                  "cycle": [node_ref(g, n, position=i) for i, n in enumerate(cycle, 1)],
                  "num_unorderable_nodes": len(blocked)}
        while _size(result) > SIZE_BUDGET and len(result["cycle"]) > 1:
            result["cycle"].pop()
        if len(cycle) <= 10:
            path = " -> ".join(f"{g.label(n)} ({n})" for n in cycle + cycle[:1])
        else:
            path = " -> ".join(f"{g.label(n)} ({n})" for n in cycle[:10]) + f" -> ... ({len(cycle)} nodes in all)"
        summary = (f"'{graph_id}' contains a cycle, so no topological order exists: {path}. "
                   f"{len(blocked)} of {n_nodes} nodes lie on or after a cycle and cannot be ordered.")
        return ok(result, summary)

    num_levels = max(level.values()) + 1
    result = {"is_dag": True,
              "num_nodes": n_nodes,
              "num_levels": num_levels,
              "order": [node_ref(g, n, position=i, level=level[n]) for i, n in enumerate(order, 1)]}

    # Check with Size_budget to ensure output is within 8Kb

    while _size(result) > SIZE_BUDGET and len(result["order"]) > 1:
        result["order"].pop()
    result["nodes_shown"] = len(result["order"])

    first, last = order[0], order[-1]
    summary = (f"'{graph_id}' is acyclic; a valid order of its {n_nodes} nodes starts with {g.label(first)} "
               f"({first}) and ends with {g.label(last)} ({last}). Nodes fall into {num_levels} level(s): "
               f"nodes on the same level have no dependency between them, and ties are broken by node id.")
    if result["nodes_shown"] < n_nodes:
        summary += f" Only the first {result['nodes_shown']} nodes of the order are listed to keep the output small."
    return ok(result, summary)

    # A tool that produces a node set or subgraph (marked with an arrow in the menu) registers it:
    #     sub_id = store.subgraph(graph_id, nodes, "Largest community of 'karate'")
    #     return ok(result, summary, result_graph_id=sub_id)
    # If it produces several node sets (e.g. communities), register each one, put its id in that
    # entry of the result as "graph_id", and return the largest one's id as result_graph_id.
