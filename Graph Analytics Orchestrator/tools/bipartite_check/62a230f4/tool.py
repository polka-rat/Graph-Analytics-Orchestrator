"""Check whether a graph is bipartite and return its two sides."""
from collections import deque

from graphkit.contract import check_top_k, error, get_graph, node_ref, ok


def _undirected_adj(g):
    adj = {n: set() for n in g.nodes()}
    self_loop = False
    for u, v, _ in g.edges():
        if u == v:
            self_loop = True
            continue
        adj[u].add(v)
        adj[v].add(u)
    return adj, self_loop


def _two_color(adj, nodes):
    color = {}
    conflict = None
    for start in nodes:
        if start in color:
            continue
        color[start] = 0
        queue = deque([start])
        while queue:
            u = queue.popleft()
            for v in adj[u]:
                if v not in color:
                    color[v] = 1 - color[u]
                    queue.append(v)
                elif color[v] == color[u]:
                    conflict = (u, v)
                    return color, conflict
    return color, conflict


def _side_payload(store, graph_id, g, nodes, name, k):
    ordered = sorted(nodes)
    listed = [node_ref(g, n) for n in ordered[:k]]
    payload = {"name": name, "size": len(ordered), "nodes": listed, "graph_id": None}
    if ordered:
        payload["graph_id"] = store.subgraph(
            graph_id, ordered, f"{name} of bipartite split of '{graph_id}'"
        )
    return payload


def run(store, graph_id, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. bipartite_check takes graph_id and top_k.")
    k, err = check_top_k(top_k)
    if err:
        return err

    nodes = g.nodes()
    if not nodes:
        return ok(
            {"is_bipartite": True, "left": {"name": "left", "size": 0, "nodes": [], "graph_id": None},
             "right": {"name": "right", "size": 0, "nodes": [], "graph_id": None}},
            "The empty graph is bipartite: both sides are empty.",
        )

    adj, self_loop = _undirected_adj(g)
    if self_loop:
        return ok(
            {"is_bipartite": False, "reason": "self-loop"},
            f"'{graph_id}' is not bipartite because it has a self-loop. "
            "Use an undirected graph with no odd cycles, such as projects.",
        )

    color, conflict = _two_color(adj, nodes)
    if conflict is not None:
        u, v = conflict
        return ok(
            {"is_bipartite": False, "reason": "odd cycle",
             "conflict": [node_ref(g, u), node_ref(g, v)]},
            f"'{graph_id}' is not bipartite: {g.label(u)} and {g.label(v)} "
            "are adjacent but would fall in the same part. Try the projects graph.",
        )

    left_nodes = [n for n in nodes if color[n] == 0]
    right_nodes = [n for n in nodes if color[n] == 1]
    left = _side_payload(store, graph_id, g, left_nodes, "left", k)
    right = _side_payload(store, graph_id, g, right_nodes, "right", k)
    if left["size"] >= right["size"]:
        result_graph_id = left["graph_id"]
        bigger = "left"
    else:
        result_graph_id = right["graph_id"]
        bigger = "right"

    kind = " (direction ignored)" if g.directed else ""
    summary = (
        f"'{graph_id}' is bipartite{kind}: left has {left['size']} nodes and "
        f"right has {right['size']} nodes. The {bigger} side is in result_graph_id."
    )
    return ok({"is_bipartite": True, "left": left, "right": right}, summary, result_graph_id)
