"""Maximum-cardinality matching of a bipartite graph with the Hopcroft-Karp algorithm.

The two sides come from a node attribute (default 'side', e.g. student/project) when it splits the
nodes into exactly two groups; otherwise they are found by 2-colouring with breadth-first search.
Directed graphs are treated as undirected; weights are ignored; runs in O(E * sqrt(V)).
"""
from collections import deque

from graphkit.contract import check_top_k, error, get_graph, node_ref, ok

INF = float("inf")


def _sides_from_attribute(g, nbrs, attr, left_value):
    values = sorted({str(g.node_attrs(v).get(attr)) for v in g.nodes() if attr in g.node_attrs(v)})
    if len(values) != 2 or any(attr not in g.node_attrs(v) for v in g.nodes()):
        return None, None
    if left_value is not None and left_value not in values:
        return None, error(f"left_side '{left_value}' is not a value of attribute '{attr}'; "
                           f"use one of: {', '.join(values)}.")
    left_value = left_value or values[0]
    left = {v for v in g.nodes() if str(g.node_attrs(v)[attr]) == left_value}
    for u in left:
        for v in nbrs[u]:
            if v in left:
                return None, error(f"Nodes '{u}' and '{v}' are both '{left_value}' but are linked, so the "
                                   f"'{attr}' attribute is not a valid bipartition. The graph is not bipartite.")
    return (left, values, left_value), None


def _sides_by_colouring(g, nbrs):
    colour = {}
    for start in sorted(g.nodes()):
        if start in colour:
            continue
        colour[start] = 0
        queue = deque([start])
        while queue:
            u = queue.popleft()
            for v in sorted(nbrs[u]):
                if v not in colour:
                    colour[v] = 1 - colour[u]
                    queue.append(v)
                elif colour[v] == colour[u]:
                    return None, error(f"Graph '{g.graph_id}' is not bipartite: nodes '{u}' and '{v}' are "
                                       f"linked and lie on an odd cycle, so no two-sided matching exists. "
                                       f"Use it on a bipartite graph such as 'projects'.")
    return {v for v, c in colour.items() if c == 0}, None


def hopcroft_karp(left, adj):
    """Maximum matching. adj[u] = sorted right-side neighbours of left node u. Returns {left: right}."""
    match_l = {u: None for u in left}
    match_r = {}
    dist = {}

    def bfs():
        queue = deque()
        for u in left:
            if match_l[u] is None:
                dist[u] = 0
                queue.append(u)
            else:
                dist[u] = INF
        found = False
        while queue:
            u = queue.popleft()
            for v in adj[u]:
                w = match_r.get(v)
                if w is None:
                    found = True
                elif dist[w] == INF:
                    dist[w] = dist[u] + 1
                    queue.append(w)
        return found

    def dfs(root):
        # iterative DFS along the BFS layers; returns True if an augmenting path was applied
        stack = [(root, iter(adj[root]))]
        path = []  # (left, right) edges on the current path
        while stack:
            u, it = stack[-1]
            advanced = False
            for v in it:
                w = match_r.get(v)
                if w is None:
                    path.append((u, v))
                    for a, b in path:
                        match_l[a] = b
                        match_r[b] = a
                    return True
                if dist[w] == dist[u] + 1:
                    path.append((u, v))
                    stack.append((w, iter(adj[w])))
                    advanced = True
                    break
            if not advanced:
                dist[u] = INF  # dead end: never try this node again in this phase
                stack.pop()
                if path:
                    path.pop()
        return False

    while bfs():
        for u in left:
            if match_l[u] is None:
                dfs(u)
    return {u: v for u, v in match_l.items() if v is not None}


def run(store, graph_id, side_attribute="side", left_side=None, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. bipartite_matching takes graph_id, "
                     f"side_attribute, left_side and top_k.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if not isinstance(side_attribute, str) or (left_side is not None and not isinstance(left_side, str)):
        return error("side_attribute and left_side must be strings, e.g. side_attribute='side', left_side='student'.")
    if g.number_of_nodes() == 0:
        return error(f"Graph '{graph_id}' has no nodes. Pick another graph.")

    nbrs = {v: set(g.undirected_neighbors(v)) for v in g.nodes()}
    loops = [v for v in g.nodes() if v in nbrs[v]]
    if loops:
        return error(f"Graph '{graph_id}' is not bipartite: node '{loops[0]}' has a self-loop.")

    sides, err = _sides_from_attribute(g, nbrs, side_attribute, left_side)
    if err:
        return err
    if sides:
        left, values, left_value = sides
        names = (left_value, next(x for x in values if x != left_value))
    else:
        if left_side is not None:
            return error(f"left_side was given but nodes have no two-valued '{side_attribute}' attribute; "
                         f"omit left_side, or set side_attribute to the attribute that names the sides.")
        left, err = _sides_by_colouring(g, nbrs)
        if err:
            return err
        names = ("side A", "side B")
    right = set(g.nodes()) - left
    if not any(nbrs[u] for u in left):
        return error(f"Graph '{graph_id}' has no edges between its two sides, so the matching is empty.")

    left_order = sorted(left)
    adj = {u: sorted(nbrs[u]) for u in left_order}
    match = hopcroft_karp(left_order, adj)
    size = len(match)
    unmatched_l = [u for u in left_order if u not in match]
    matched_r = set(match.values())
    unmatched_r = sorted(v for v in right if v not in matched_r)

    pairs = sorted(match.items())
    result = {
        "matching_size": size,
        "left_side": names[0], "right_side": names[1],
        "left_size": len(left), "right_size": len(right),
        "perfect": not unmatched_l and not unmatched_r,
        "pairs": [{"left": node_ref(g, u), "right": node_ref(g, v)} for u, v in pairs[:k]],
        "unmatched_left": [node_ref(g, u) for u in unmatched_l[:k]],
        "unmatched_right": [node_ref(g, v) for v in unmatched_r[:k]],
    }
    if size > k:
        result["note"] = f"Only the first {k} of {size} pairs are listed; raise top_k (max 100) to see more."
    summary = (f"A maximum matching of '{graph_id}' pairs {size} {names[0]} node(s) with {names[1]} node(s); "
               f"{len(unmatched_l)} of {len(left)} {names[0]} and {len(unmatched_r)} of {len(right)} "
               f"{names[1]} nodes stay unmatched.")
    return ok(result, summary)
