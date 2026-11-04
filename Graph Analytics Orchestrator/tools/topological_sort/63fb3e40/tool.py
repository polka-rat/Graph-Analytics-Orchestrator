"""Topological sort: an order of a directed acyclic graph's nodes, or a cycle if there is one.

Uses Kahn's algorithm, peeling the graph into stages: stage 1 holds the nodes with no incoming
edges, stage 2 the nodes whose predecessors are all in stage 1, and so on (the same grouping as
NetworkX's topological_generations). Nodes are listed by (stage, id), which is a valid topological
order and is deterministic. If some nodes are never freed, the graph has a cycle; the tool then
returns a shortest cycle through one of the blocked nodes. With `node`, only that node and its
ancestors (everything that must come before it) are ordered. Runs in O(n log n + m) time.
"""
import json
from collections import deque

from graphkit.contract import MAX_OUTPUT_BYTES, check_node, check_top_k, error, get_graph, node_ref, ok

DEFAULT_TOP_K = 100
SIZE_MARGIN = 512       # room left under the 8 KB limit for the summary and keys
MAX_CYCLE_NODES = 100   # a longer cycle is cut short (the length is still reported)


def _ancestors(g, node):
    """`node` and every node with a directed path to it."""
    seen = {node}
    queue = deque([node])
    while queue:
        for u in g.in_neighbors(queue.popleft()):
            if u not in seen:
                seen.add(u)
                queue.append(u)
    return seen


def _stages(g, scope):
    """Kahn's algorithm on the subgraph induced by `scope`.

    Returns ({node: stage}, blocked) where stages start at 1 and `blocked` is the set of nodes that
    could not be ordered because they lie on, or after, a cycle.
    """
    indeg = {v: sum(1 for u in g.in_neighbors(v) if u in scope) for v in scope}
    stage = {}
    current = sorted(v for v, d in indeg.items() if d == 0)
    level = 1
    while current:
        nxt = []
        for u in current:
            stage[u] = level
            for v in g.out_neighbors(u):
                if v in scope:
                    indeg[v] -= 1
                    if indeg[v] == 0:
                        nxt.append(v)
        current = sorted(nxt)
        level += 1
    return stage, set(scope) - set(stage)


def _find_cycle(g, blocked):
    """A shortest directed cycle through a node of `blocked`, as a list [v1, v2, ..., vk] (vk -> v1).

    Every blocked node has a blocked predecessor, so walking backwards from the smallest blocked
    node must repeat a node; that node is on a cycle, and a BFS from it finds the shortest cycle
    through it. Choosing the smallest id at each step keeps the answer deterministic.
    """
    v = min(blocked)
    seen = set()
    while v not in seen:
        seen.add(v)
        v = min(u for u in g.in_neighbors(v) if u in blocked)
    start = v
    if g.has_edge(start, start):
        return [start]
    parent = {start: None}
    queue = deque([start])
    while queue:
        u = queue.popleft()
        for w in sorted(g.out_neighbors(u)):
            if w not in blocked:
                continue
            if w == start:
                path = [u]
                while parent[path[-1]] is not None:
                    path.append(parent[path[-1]])
                return path[::-1]
            if w not in parent:
                parent[w] = u
                queue.append(w)
    return [start]  # unreachable: start lies on a cycle


def _fits(payload):
    return len(json.dumps(payload).encode("utf-8")) <= MAX_OUTPUT_BYTES - SIZE_MARGIN


def _names(entries, limit=5):
    names = ", ".join(e["label"] for e in entries[:limit])
    return names + (", ..." if len(entries) > limit else "")


def run(store, graph_id, node=None, top_k=DEFAULT_TOP_K, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     f"topological_sort takes graph_id, node and top_k.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if not g.directed:
        return error(f"Graph '{graph_id}' is undirected, and a topological order only exists for a "
                     f"directed graph. Use list_graphs to pick a directed graph such as 'courses'.")
    if g.number_of_nodes() == 0:
        return error(f"Graph '{graph_id}' has no nodes, so there is nothing to order. "
                     f"Use list_graphs to pick another graph.")
    if node is not None:
        err = check_node(g, node)
        if err:
            return err

    scope = _ancestors(g, node) if node is not None else set(g.nodes())
    stage, blocked = _stages(g, scope)
    target = node_ref(g, node) if node is not None else None
    where = f"the prerequisites of {target['label']}" if target else f"'{graph_id}'"

    if blocked:
        cycle = _find_cycle(g, blocked)
        shown = cycle[:MAX_CYCLE_NODES]
        result = {
            "graph_id": graph_id,
            "is_dag": False,
            "target": target,
            "number_of_nodes": len(scope),
            "blocked_nodes": len(blocked),
            "cycle_length": len(cycle),
            "cycle": [node_ref(g, v, position=i) for i, v in enumerate(shown, 1)],
            "cycle_truncated": len(shown) < len(cycle),
        }
        while not _fits(result):
            result["cycle"].pop()
            result["cycle_truncated"] = True
        loop = " -> ".join(e["label"] for e in result["cycle"][:6])
        loop += " -> ..." if result["cycle_truncated"] or len(cycle) > 6 else f" -> {result['cycle'][0]['label']}"
        summary = (f"No topological order exists for {where} because it contains a cycle: {len(blocked)} of "
                   f"{len(scope)} nodes lie on or after a cycle. A shortest cycle found has {len(cycle)} "
                   f"node(s): {loop}.")
        return ok(result, summary)

    ordered = sorted(scope, key=lambda v: (stage[v], v))
    n_stages = max(stage.values())
    order = [node_ref(g, v, position=i, stage=stage[v]) for i, v in enumerate(ordered[:k], 1)]
    result = {
        "graph_id": graph_id,
        "is_dag": True,
        "target": target,
        "number_of_nodes": len(scope),
        "number_of_stages": n_stages,
        "stage_sizes": [sum(1 for v in scope if stage[v] == s) for s in range(1, n_stages + 1)],
        "order": order,
        "returned": len(order),
        "truncated": len(order) < len(scope),
    }
    shrunk = False
    while not _fits(result):
        result["order"].pop()
        result["returned"] -= 1
        result["truncated"] = shrunk = True

    first = [e for e in order if e["stage"] == 1]
    summary = (f"{where[0].upper() + where[1:]} can be ordered in {n_stages} stage(s) covering "
               f"{len(scope)} node(s); stage 1 (no prerequisites) is {_names(first)}.")
    if target:
        summary += f" {target['label']} comes last, in stage {stage[node]}."
    if result["truncated"]:
        summary += (f" Only the first {result['returned']} nodes are listed"
                    f"{' to keep the output small' if shrunk else ''}; raise top_k (max 100) or pass a node to see more.")
    return ok(result, summary)
