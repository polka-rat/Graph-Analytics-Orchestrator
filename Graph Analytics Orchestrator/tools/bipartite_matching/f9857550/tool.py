"""Maximum matching of a bipartite graph with the Hopcroft-Karp algorithm.

1. Split the nodes into two sides: by a node attribute (e.g. 'side') if the caller
   names one, else by 2-colouring each connected component with BFS.
2. Hopcroft-Karp: repeat { BFS from all free left nodes to layer the graph by
   shortest alternating paths; DFS along the layers to find a maximal set of
   vertex-disjoint shortest augmenting paths, and flip them } until no augmenting
   path is left. Runs in O(E * sqrt(V)).
"""
from collections import deque

from graphkit.contract import check_top_k, error, get_graph, node_ref, ok

INF = float("inf")


def _two_colour(g):
    """{node: 0 or 1} by BFS 2-colouring, or (None, (u, v)) for an edge inside one side."""
    colour = {}
    for start in sorted(g.nodes()):
        if start in colour:
            continue
        colour[start] = 0
        queue = deque([start])
        while queue:
            u = queue.popleft()
            for v in g.neighbors(u):
                if v not in colour:
                    colour[v] = 1 - colour[u]
                    queue.append(v)
                elif colour[v] == colour[u]:
                    return None, (u, v)
    return colour, None


def _hopcroft_karp(left, adj):
    """Maximum matching. left: sorted left nodes; adj: {left node: sorted right neighbours}."""
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
        # Iterative DFS along the BFS layers, so deep paths cannot hit the recursion limit.
        stack = [(root, iter(adj[root]))]
        path = []
        while stack:
            u, it = stack[-1]
            advanced = False
            for v in it:
                w = match_r.get(v)
                if w is None:
                    # Augmenting path found: flip every edge on it.
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
                dist[u] = INF  # dead end: never visit again in this phase
                stack.pop()
                if path:
                    path.pop()
        return False

    while bfs():
        for u in left:
            if match_l[u] is None:
                dfs(u)
    return match_l


def run(store, graph_id, top_k=10, side_attribute=None, left_value=None, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. bipartite_matching takes graph_id, top_k, "
                     f"side_attribute and left_value.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if g.directed:
        return error(f"Graph '{graph_id}' is directed; bipartite_matching needs an undirected bipartite graph "
                     f"such as 'projects'. Use list_graphs to find one.")
    if g.number_of_edges() == 0:
        return error(f"Graph '{graph_id}' has no edges, so nothing can be matched.")
    if left_value is not None and side_attribute is None:
        return error("left_value needs side_attribute too, e.g. side_attribute='side', left_value='student'.")

    nodes = sorted(g.nodes())
    if side_attribute is not None:
        if not isinstance(side_attribute, str) or any(side_attribute not in g.node_attrs(n) for n in nodes):
            return error(f"Not every node of '{graph_id}' has attribute {side_attribute!r}. "
                         f"Use node_attributes to see which attributes exist, or omit side_attribute.")
        values = sorted({str(g.node_attrs(n)[side_attribute]) for n in nodes})
        if len(values) != 2:
            return error(f"Attribute {side_attribute!r} must take exactly two values to split the graph; "
                         f"it takes {len(values)}: {values[:5]}.")
        if left_value is None:
            left_value = values[0]
        if str(left_value) not in values:
            return error(f"left_value {left_value!r} is not a value of {side_attribute!r}; use one of {values}.")
        side = {n: 0 if str(g.node_attrs(n)[side_attribute]) == str(left_value) else 1 for n in nodes}
        for u, v, _ in g.edges():
            if side[u] == side[v]:
                return error(f"Edge {u}-{v} joins two nodes on the same side of {side_attribute!r}, "
                             f"so that split is not bipartite.")
    else:
        side, bad = _two_colour(g)
        if side is None:
            u, v = bad
            return error(f"Graph '{graph_id}' is not bipartite: it has an odd cycle through the edge {u}-{v}. "
                         f"Maximum matching here needs an undirected bipartite graph such as 'projects'.")

    left = [n for n in nodes if side[n] == 0]
    adj = {u: sorted(g.neighbors(u)) for u in left}
    match_l = _hopcroft_karp(left, adj)

    pairs = sorted((u, v) for u, v in match_l.items() if v is not None)
    size = len(pairs)
    n_left, n_right = len(left), len(nodes) - len(left)
    result = {
        "matching_size": size,
        "left_side_size": n_left,
        "right_side_size": n_right,
        "unmatched_left": n_left - size,
        "unmatched_right": n_right - size,
        "is_perfect": size == n_left == n_right,
        "pairs": [{"left": node_ref(g, u), "right": node_ref(g, v)} for u, v in pairs[:k]],
        "pairs_truncated": size > k,
    }
    shown = ", ".join(f"{g.label(u)} - {g.label(v)}" for u, v in pairs[:3])
    summary = (f"A maximum matching in '{graph_id}' pairs {size} of {n_left} left-side and {n_right} right-side "
               f"nodes ({n_left - size} left and {n_right - size} right left unmatched), e.g. {shown}.")
    return ok(result, summary)
