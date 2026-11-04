"""Maximum-cardinality matching in a bipartite graph with the Hopcroft-Karp algorithm."""
import json
from collections import deque

from graphkit.contract import MAX_OUTPUT_BYTES, check_top_k, error, get_graph, node_ref, ok

INF = float("inf")


def _sides(g):
    """Split the nodes into two sides.

    Uses the node attribute 'side' when every node has one of exactly two values and every edge
    crosses between them; otherwise 2-colours each component by BFS.
    Returns (left, right, left_name, right_name, None) or (None, None, None, None, odd_cycle_edge).
    """
    nodes = sorted(g.nodes())
    values = {g.node_attrs(n).get("side") for n in nodes}
    if len(values) == 2 and None not in values and all(isinstance(v, str) for v in values):
        if all(g.node_attrs(u)["side"] != g.node_attrs(v)["side"] for u, v, _ in g.edges()):
            a, b = sorted(values)
            left = [n for n in nodes if g.node_attrs(n)["side"] == a]
            right = [n for n in nodes if g.node_attrs(n)["side"] == b]
            return left, right, a, b, None

    colour = {}
    for start in nodes:
        if start in colour:
            continue
        colour[start] = 0
        queue = deque([start])
        while queue:
            u = queue.popleft()
            for v in sorted(g.undirected_neighbors(u)):
                if v not in colour:
                    colour[v] = 1 - colour[u]
                    queue.append(v)
                elif colour[v] == colour[u]:
                    return None, None, None, None, (u, v)
    left = [n for n in nodes if colour[n] == 0]
    right = [n for n in nodes if colour[n] == 1]
    return left, right, "side_A", "side_B", None


def _hopcroft_karp(left, adj):
    """adj: left node -> sorted list of right neighbours. Returns {left: right} for matched pairs."""
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

    def augment(root, ptr):
        """Iterative DFS along the BFS layers; flips one shortest augmenting path if found."""
        stack = [root]
        while stack:
            u = stack[-1]
            advanced = False
            while ptr[u] < len(adj[u]):
                v = adj[u][ptr[u]]
                ptr[u] += 1
                w = match_r.get(v)
                if w is None:
                    # Free right node: flip the path root -> ... -> u -> v.
                    cur = v
                    for x in reversed(stack):
                        prev = match_l[x]
                        match_l[x] = cur
                        match_r[cur] = x
                        cur = prev
                    return True
                if dist[w] == dist[u] + 1:
                    stack.append(w)
                    advanced = True
                    break
            if not advanced:
                dist[u] = INF  # dead end for this phase
                stack.pop()
        return False

    while bfs():
        ptr = {u: 0 for u in left}
        for u in left:
            if match_l[u] is None:
                augment(u, ptr)
    return {u: v for u, v in match_l.items() if v is not None}


def run(store, graph_id, top_k=100, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. bipartite_matching takes graph_id and top_k.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if g.directed:
        return error(f"Graph '{graph_id}' is directed; bipartite matching needs an undirected bipartite graph "
                     f"such as 'projects'. Use list_graphs to find one.")
    if g.number_of_nodes() == 0:
        return error(f"Graph '{graph_id}' has no nodes. Use list_graphs to pick another graph.")

    left, right, lname, rname, odd = _sides(g)
    if odd is not None:
        u, v = odd
        return error(f"Graph '{graph_id}' is not bipartite: an odd cycle passes through the edge "
                     f"{g.label(u)} ({u}) - {g.label(v)} ({v}), so its nodes cannot be split into two "
                     f"groups. Use a bipartite graph such as 'projects', or run bipartite_check first.")

    adj = {u: sorted(g.undirected_neighbors(u)) for u in left}
    matching = _hopcroft_karp(left, adj)
    size = len(matching)

    pairs_all = sorted(matching.items())
    matched_right = set(matching.values())
    unmatched_left = [u for u in left if u not in matching]
    unmatched_right = [v for v in right if v not in matched_right]
    upper = min(len(left), len(right))
    perfect = size == len(left) == len(right)

    # Shrink the lists until the output fits in 8 KB.
    for limit in (k, 50, 25, 10, 5, 0):
        limit = min(limit, k)
        result = {
            "matching_size": size,
            "left_side": lname, "right_side": rname,
            "left_count": len(left), "right_count": len(right),
            "max_possible": upper, "perfect": perfect,
            "pairs": [{lname: node_ref(g, u), rname: node_ref(g, v)} for u, v in pairs_all[:limit]],
            "pairs_truncated": len(pairs_all) > limit,
            "unmatched": {lname: [node_ref(g, u) for u in unmatched_left[:limit]],
                          rname: [node_ref(g, v) for v in unmatched_right[:limit]]},
            "unmatched_counts": {lname: len(unmatched_left), rname: len(unmatched_right)},
        }
        if len(json.dumps(result).encode("utf-8")) < MAX_OUTPUT_BYTES - 1000:
            break

    if size == 0:
        summary = f"'{graph_id}' has no edges between its two sides, so no pairs can be matched."
    else:
        summary = (f"A maximum matching in '{graph_id}' pairs {size} {lname}(s) with {size} {rname}(s) "
                   f"(at most {upper} were possible); {len(unmatched_left)} {lname}(s) and "
                   f"{len(unmatched_right)} {rname}(s) stay unmatched.")
        if perfect:
            summary = f"'{graph_id}' has a perfect matching: all {size} pairs cover every node."
    return ok(result, summary)
