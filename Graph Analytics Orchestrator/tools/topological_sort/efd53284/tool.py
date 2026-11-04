"""Topological order of a directed graph, or a directed cycle if one exists.
"""
import heapq

from graphkit.contract import error, get_graph, node_ref, ok


def _find_cycle(g):
    """Return one directed cycle as [v0, v1, ..., vk], or [] if none exists."""
    color = {node: 0 for node in g.nodes()}  # 0=unvisited, 1=on stack, 2=done
    parent = {}
    for start in g.nodes():
        if color[start] != 0:
            continue
        color[start] = 1
        stack = [(start, iter(g.out_neighbors(start)))]
        while stack:
            node, neighbours = stack[-1]
            advanced = False
            for nxt in neighbours:
                if color[nxt] == 0:
                    parent[nxt] = node
                    color[nxt] = 1
                    stack.append((nxt, iter(g.out_neighbors(nxt))))
                    advanced = True
                    break
                if color[nxt] == 1:
                    path = [node]
                    current = node
                    while current != nxt:
                        current = parent[current]
                        path.append(current)
                    path.reverse()
                    return path
            if not advanced:
                color[node] = 2
                stack.pop()
    return []


def run(store, graph_id, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(
            f"Unknown parameter(s): {', '.join(params)}. "
            "topological_sort takes only graph_id."
        )
    if not g.directed:
        return error(
            f"Graph '{graph_id}' is undirected, so it has no topological order. "
            "Use a directed graph such as 'courses' or 'airports'."
        )
    if g.number_of_nodes() == 0:
        return error(f"Graph '{graph_id}' has no nodes.")

    indegree = {node: len(g.in_neighbors(node)) for node in g.nodes()}
    ready = [node for node in g.nodes() if indegree[node] == 0]
    heapq.heapify(ready)
    order = []

    while ready:
        node = heapq.heappop(ready)
        order.append(node)
        for nxt in g.out_neighbors(node):
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                heapq.heappush(ready, nxt)

    if len(order) == g.number_of_nodes():
        result = [
            node_ref(g, node, position=position)
            for position, node in enumerate(order, 1)
        ]
        summary = (
            f"Topological order of {len(order)} nodes in '{graph_id}': "
            f"{g.label(order[0])} comes first and {g.label(order[-1])} last."
        )
        return ok(result, summary)

    cycle = _find_cycle(g)
    if not cycle:
        return error(
            f"Graph '{graph_id}' is not acyclic, but no cycle could be extracted. "
            "This should not happen for a finite directed graph."
        )

    result = [
        node_ref(g, node, position=position, cycle=True)
        for position, node in enumerate(cycle, 1)
    ]
    path = " -> ".join(f"{g.label(node)} ({node})" for node in cycle)
    summary = (
        f"Graph '{graph_id}' is not acyclic. One directed cycle is: "
        f"{path} -> {g.label(cycle[0])} ({cycle[0]})."
    )
    return ok(result, summary)
