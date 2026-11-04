"""Maximum-cardinality bipartite matching with the Hopcroft-Karp algorithm.

1. Split the nodes into two sides: use the node attribute 'side' when it gives a valid
   2-way split (as in 'projects'), otherwise 2-colour the graph with BFS. A graph that
   cannot be 2-coloured has an odd cycle and is not bipartite.
2. Hopcroft-Karp: repeatedly BFS from the free left nodes to build layers, then DFS to find
   a maximal set of vertex-disjoint shortest augmenting paths, and flip them.
   O(m * sqrt(n)) time.
"""
import json
from collections import deque

from graphkit.contract import MAX_OUTPUT_BYTES, error, get_graph, node_ref, ok

INF = float("inf")


def _fits(out):
    """True if the response stays under the contract's 8 KB limit."""
    return len(json.dumps(out, sort_keys=True).encode("utf-8")) <= MAX_OUTPUT_BYTES


def _split_by_attribute(g):
    """Use the 'side' attribute if every node has one, there are exactly two values,
    and every edge joins the two sides. Returns (left, right, left_name, right_name) or None."""
    nodes = g.nodes()
    sides = {}
    for u in nodes:
        s = g.node_attrs(u).get("side")
        if s is None:
            return None
        sides[u] = s
    values = list(dict.fromkeys(sides[u] for u in nodes))  # in node order
    if len(values) != 2:
        return None
    for u, v, _ in g.edges():
        if sides[u] == sides[v]:
            return None
    left_name, right_name = values  # the side of the first node is the left side
    left = [u for u in nodes if sides[u] == left_name]
    right = [u for u in nodes if sides[u] == right_name]
    return left, right, str(left_name), str(right_name)


def _two_colour(g):
    """BFS 2-colouring. Returns (left, right, None) or (None, None, (u, v)) for a clashing edge."""
    colour = {}
    for start in g.nodes():  # fixed node order -> deterministic sides
        if start in colour:
            continue
        colour[start] = 0
        queue = deque([start])
        while queue:
            u = queue.popleft()
            for v in g.out_neighbors(u):
                if v not in colour:
                    colour[v] = 1 - colour[u]
                    queue.append(v)
                elif colour[v] == colour[u]:
                    return None, None, (u, v)
    left = [u for u in g.nodes() if colour[u] == 0]
    right = [u for u in g.nodes() if colour[u] == 1]
    return left, right, None


def _hopcroft_karp(left, adj):
    """Maximum matching. adj[u] lists the right-side neighbours of left node u."""
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
                    found = True  # a free right node: an augmenting path exists
                elif dist[w] == INF:
                    dist[w] = dist[u] + 1
                    queue.append(w)
        return found

    def dfs(root):
        """Iterative DFS along the BFS layers; augments and returns True if it finds a path."""
        stack = [(root, iter(adj[root]))]
        chosen = []  # chosen[i] is the right node taken from stack[i]
        while stack:
            u, it = stack[-1]
            pushed = False
            for v in it:
                w = match_r.get(v)
                if w is None:
                    chosen.append(v)
                    for (x, _), y in zip(stack, chosen):  # flip the path
                        match_l[x] = y
                        match_r[y] = x
                    return True
                if dist.get(w) == dist[u] + 1:
                    chosen.append(v)
                    stack.append((w, iter(adj[w])))
                    pushed = True
                    break
            if not pushed:
                dist[u] = INF  # dead end: do not visit again in this phase
                stack.pop()
                if chosen:
                    chosen.pop()
        return False

    while bfs():
        for u in left:
            if match_l[u] is None:
                dfs(u)
    return match_l


def run(store, graph_id, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. bipartite_matching takes only graph_id.")
    if g.directed:
        return error(f"Graph '{graph_id}' is directed, but bipartite_matching needs an undirected bipartite "
                     f"graph (for example 'projects'). Use list_graphs to find one.")
    if g.number_of_edges() == 0:
        return ok([], f"Graph '{graph_id}' has no edges, so the maximum matching is empty (size 0).")

    split = _split_by_attribute(g)
    if split:
        left, right, left_name, right_name = split
    else:
        left, right, clash = _two_colour(g)
        if clash:
            u, v = clash
            return error(f"Graph '{graph_id}' is not bipartite: the edge {u}-{v} closes an odd cycle, so the "
                         f"nodes cannot be split into two sides. Use an undirected bipartite graph such as "
                         f"'projects'.")
        left_name, right_name = "left-side", "right-side"

    right_set = set(right)
    adj = {u: sorted(v for v in g.out_neighbors(u) if v in right_set) for u in left}
    match_l = _hopcroft_karp(left, adj)

    pairs = sorted((u, v) for u, v in match_l.items() if v is not None)
    size = len(pairs)
    summary = (f"A maximum matching has {size} pairs, matching {size} of {len(left)} {left_name} nodes "
               f"with {size} of {len(right)} {right_name} nodes; {len(left) - size} {left_name} and "
               f"{len(right) - size} {right_name} nodes stay unmatched.")

    def build(items, note=""):
        return ok([{"left": node_ref(g, u), "right": node_ref(g, v)} for u, v in items], summary + note)

    out = build(pairs)
    shown = size
    while shown > 1 and not _fits(out):  # keep the response under 8 KB
        shown -= 1
        out = build(pairs[:shown], f" Listing the first {shown} pairs to stay under 8 KB.")
    return out
