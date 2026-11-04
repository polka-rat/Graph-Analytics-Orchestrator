"""Articulation points and bridges (Tarjan's low-link DFS); edge direction is ignored."""
import json

from graphkit.contract import MAX_OUTPUT_BYTES, check_top_k, error, get_graph, node_ref, ok


def find_cuts(g):
    """Articulation points (set) and bridges (list of (u, v)) of the undirected view of g."""
    adj = {u: sorted(v for v in g.undirected_neighbors(u) if v != u) for u in g.nodes()}
    disc, low, parent = {}, {}, {}
    points, bridges = set(), []
    timer = 0

    for root in sorted(adj):
        if root in disc:
            continue
        parent[root] = None
        disc[root] = low[root] = timer
        timer += 1
        root_children = 0
        stack = [(root, iter(adj[root]))]
        while stack:
            u, it = stack[-1]
            for v in it:
                if v not in disc:
                    parent[v] = u
                    disc[v] = low[v] = timer
                    timer += 1
                    if u == root:
                        root_children += 1
                    stack.append((v, iter(adj[v])))
                    break
                if v != parent[u]:
                    low[u] = min(low[u], disc[v])
            else:
                stack.pop()
                p = parent[u]
                if p is not None:
                    low[p] = min(low[p], low[u])
                    if low[u] > disc[p]:
                        bridges.append((p, u))
                    if p != root and low[u] >= disc[p]:
                        points.add(p)
        if root_children >= 2:
            points.add(root)
    return points, bridges


def run(store, graph_id, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     f"articulation_points_bridges takes graph_id and top_k.")
    k, err = check_top_k(top_k)
    if err:
        return err

    points, bridges = find_cuts(g)
    points = sorted(points)
    bridges = sorted(tuple(sorted(e)) for e in bridges)

    def build(count):
        result = {"articulation_point_count": len(points), "bridge_count": len(bridges),
                  "articulation_points": [node_ref(g, u) for u in points[:count]],
                  "bridges": [[node_ref(g, u), node_ref(g, v)] for u, v in bridges[:count]]}
        return ok(result, summarize(g, graph_id, points, bridges, count))

    count = k
    out = build(count)
    while count > 1 and len(json.dumps(out, sort_keys=True).encode("utf-8")) > MAX_OUTPUT_BYTES:
        count -= 1
        out = build(count)
    return out


def summarize(g, graph_id, points, bridges, shown):
    a, b = len(points), len(bridges)
    if a == 0 and b == 0:
        text = (f"'{graph_id}' has no articulation points and no bridges: removing any single node "
                f"or edge does not disconnect it.")
    else:
        text = (f"'{graph_id}' has {a} articulation point{'s' if a != 1 else ''} and "
                f"{b} bridge{'s' if b != 1 else ''}.")
        if a:
            names = ", ".join(f"{g.label(u)} ({u})" for u in points[:3])
            text += f" Articulation points include {names}."
        if shown < max(a, b):
            text += f" Up to {shown} of each are listed."
    if g.directed:
        text += " Edge direction was ignored."
    return text
