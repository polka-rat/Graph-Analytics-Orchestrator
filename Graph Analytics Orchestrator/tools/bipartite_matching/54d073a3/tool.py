"""bipartite_matching: maximum cardinality matching of a bipartite graph (Hopcroft-Karp).

Steps: (1) 2-colour the graph by breadth-first search; if an edge joins two nodes of the same
colour the graph is not bipartite and an error is returned. (2) Run Hopcroft-Karp: repeat
{a breadth-first search that layers the graph from the free left nodes, then depth-first
searches that find a maximal set of shortest vertex-disjoint augmenting paths} until no
augmenting path exists. Time O(E * sqrt(V)). Edge direction and weights are ignored.
"""
import json
from collections import deque

from graphkit.contract import MAX_OUTPUT_BYTES, check_top_k, error, get_graph, node_ref, ok


def _two_colour(nodes, adj):
    """Return (colour, None) with colour 0/1 per node, or (None, (u, v)) for an offending edge."""
    colour = {}
    for start in nodes:  # nodes are sorted, so the colouring is deterministic
        if start in colour:
            continue
        colour[start] = 0
        queue = deque([start])
        while queue:
            u = queue.popleft()
            for v in adj[u]:
                if v == u:
                    return None, (u, u)
                if v not in colour:
                    colour[v] = 1 - colour[u]
                    queue.append(v)
                elif colour[v] == colour[u]:
                    return None, (u, v)
    return colour, None


def _hopcroft_karp(left, adj):
    """Maximum matching. `left` is a sorted list; adj[u] is a sorted list of right neighbours."""
    match_l = {u: None for u in left}
    match_r = {}
    inf = float("inf")
    while True:
        # --- BFS: layer the left nodes, starting from the free ones ---
        dist = {}
        queue = deque()
        for u in left:
            if match_l[u] is None:
                dist[u] = 0
                queue.append(u)
        limit = inf  # layer at which a free right node is first reached
        while queue:
            u = queue.popleft()
            if dist[u] >= limit:
                continue
            for v in adj[u]:
                w = match_r.get(v)
                if w is None:
                    limit = dist[u]
                elif w not in dist:
                    dist[w] = dist[u] + 1
                    queue.append(w)
        if limit == inf:
            break  # no augmenting path is left: the matching is maximum

        # --- DFS (iterative): augment along shortest vertex-disjoint paths ---
        pointer = {u: 0 for u in left}
        for root in left:
            if match_l[root] is not None:
                continue
            stack = [root]   # left nodes on the current path
            chosen = []      # chosen[i] = right node used to leave stack[i]
            while stack:
                u = stack[-1]
                moved = False
                while pointer[u] < len(adj[u]):
                    v = adj[u][pointer[u]]
                    pointer[u] += 1
                    w = match_r.get(v)
                    if w is None:
                        if dist[u] == limit:  # a free right node at the right depth: augment
                            chosen.append(v)
                            for a, b in zip(stack, chosen):
                                match_l[a] = b
                                match_r[b] = a
                            stack = []
                            moved = True
                            break
                    elif dist.get(w) == dist[u] + 1:
                        chosen.append(v)
                        stack.append(w)
                        moved = True
                        break
                if not moved:  # dead end: remove u from this phase and backtrack
                    dist[u] = inf
                    stack.pop()
                    if chosen:
                        chosen.pop()
    return match_l


def run(store, graph_id, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. bipartite_matching takes graph_id and top_k.")
    k, err = check_top_k(top_k)
    if err:
        return err

    nodes = sorted(g.nodes())
    n = len(nodes)
    if n == 0:
        return error(f"Graph '{graph_id}' has no nodes, so there is nothing to match.")

    adj = {v: sorted(g.undirected_neighbors(v)) for v in nodes}  # direction is ignored
    colour, bad = _two_colour(nodes, adj)
    if colour is None:
        u, v = bad
        what = f"node {u!r} has an edge to itself" if u == v else f"nodes {u!r} and {v!r} are joined by an edge but fall on the same side"
        return error(f"Graph '{graph_id}' is not bipartite ({what}), so bipartite matching does not apply. "
                     f"Try a bipartite graph such as 'projects' (students and projects).")

    left = [v for v in nodes if colour[v] == 0]
    n_right = n - len(left)
    match_l = _hopcroft_karp(left, {u: adj[u] for u in left})

    pairs = [(u, match_l[u]) for u in left if match_l[u] is not None]  # sorted by left id
    size = len(pairs)
    matched = {x for pair in pairs for x in pair}
    unmatched = [v for v in nodes if v not in matched]
    perfect = size * 2 == n

    pair_entries = [{"left": node_ref(g, u), "right": node_ref(g, v)} for u, v in pairs[:k]]
    unmatched_entries = [node_ref(g, v, side="left" if colour[v] == 0 else "right") for v in unmatched[:k]]
    result = {
        "matching_size": size,
        "is_perfect_matching": perfect,
        "left_size": len(left),
        "right_size": n_right,
        "num_unmatched": len(unmatched),
        "pairs": pair_entries,
        "unmatched": unmatched_entries,
    }
    # Keep the whole response under the size limit.
    while len(json.dumps(result)) > MAX_OUTPUT_BYTES - 600 and (len(result["pairs"]) > 1 or result["unmatched"]):
        if len(result["unmatched"]) >= len(result["pairs"]) and result["unmatched"]:
            result["unmatched"] = result["unmatched"][:-1]
        else:
            result["pairs"] = result["pairs"][:-1]

    summary = (f"Maximum matching of '{graph_id}' has {size} pairs "
               f"({len(left)} nodes on one side, {n_right} on the other); "
               f"{'it is perfect' if perfect else str(len(unmatched)) + ' nodes stay unmatched'}.")
    if len(result["pairs"]) < size:
        summary += f" Listing {len(result['pairs'])} of the {size} pairs."
    return ok(result, summary)
