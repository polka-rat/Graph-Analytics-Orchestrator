"""Maximum matching of a bipartite graph by the Hopcroft-Karp algorithm: the most pairs with no node used twice.

Rules (the validator checks them):
- Implement the algorithm yourself: standard library, NumPy and graphkit only.
- Get graphs only from the store; never open files, print, or use the network.
- Never crash: return error("what went wrong and how to fix it") instead.
- Return every node as node_ref(g, node, ...), so it has both an id and a label.
- Keep the output under 8 KB: respect top_k.
- Be deterministic: same input, same output. Randomised algorithms take a `seed` parameter (default 0).
"""
from graphkit.contract import MAX_OUTPUT_BYTES, check_top_k, error, get_graph, node_ref, ok
from collections import deque
import json


def sides_from_attribute(g):
    side = {}
    for n in g.nodes():
        if "side" not in g.node_attrs(n):
            return None
        side[n] = str(g.node_attrs(n)["side"])
    if len(set(side.values())) != 2:
        return None
    for u, v, w in g.edges():
        if side[u] == side[v]:
            return None
    return side


def two_colour(g):
    colour = {}
    for start in sorted(g.nodes()):
        if start in colour:
            continue
        colour[start] = 0
        q = deque([start])
        while q:
            u = q.popleft()
            for v in sorted(g.undirected_neighbors(u)):
                if v not in colour:
                    colour[v] = 1 - colour[u]
                    q.append(v)
                elif colour[v] == colour[u]:
                    return None, (u, v)
    return colour, None


def augment(start, adj, match_l, match_r, dist, limit):
    stack = [start]
    via = []
    nxt = {start: 0}
    while stack:
        u = stack[-1]
        if nxt[u] == len(adj[u]):
            dist[u] = None 
            stack.pop()
            if via:
                via.pop()
            continue
        v = adj[u][nxt[u]]
        nxt[u] = nxt[u] + 1
        w = match_r[v]
        if w is None and dist[u] == limit:
            via.append(v)
            for i in range(len(stack)):
                match_l[stack[i]] = via[i]
                match_r[via[i]] = stack[i]
            return True
        if w is not None and dist.get(w) is not None and dist[w] == dist[u] + 1:
            via.append(v)
            stack.append(w)
            nxt[w] = 0
    return False


def hopcroft_karp(adj, left, right):
    match_l = {}
    for u in left:
        match_l[u] = None
    match_r = {}
    for v in right:
        match_r[v] = None

    while True:
        # BFS from all free left nodes: dist = layer; limit = layer where a free right node is first seen
        dist = {}
        q = deque()
        for u in left:
            if match_l[u] is None:
                dist[u] = 0
                q.append(u)
        limit = None
        while q:
            u = q.popleft()
            if limit is not None and dist[u] > limit:
                continue
            for v in adj[u]:
                w = match_r[v]
                if w is None:
                    if limit is None:
                        limit = dist[u]
                elif w not in dist:
                    dist[w] = dist[u] + 1
                    q.append(w)
        if limit is None:
            break  # no augmenting path left: the matching is maximum

        for u in left:
            if match_l[u] is None and dist.get(u) == 0:
                augment(u, adj, match_l, match_r, dist, limit)

    return match_l


def run(store, graph_id, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. bipartite_matching takes graph_id and top_k.")
    top_k, err = check_top_k(top_k)
    if err:
        return err
    if g.number_of_nodes() == 0:
        return error(f"Graph '{graph_id}' has no nodes, so there is nothing to match.")

    side = sides_from_attribute(g)
    if side is not None:
        names = sorted(set(side.values()))
    else:
        names = ["side A", "side B"]  # both sides exist even if one ends up empty (e.g. no edges)
        colour, bad_edge = two_colour(g)
        if colour is None:
            u, v = bad_edge
            return error(f"Graph '{graph_id}' is not bipartite: it has an odd cycle (for example through the edge "
                         f"{u}-{v}), so its nodes cannot be split into two groups. Use a bipartite graph such as "
                         f"'projects', or run bipartite_check first.")
        side = {}
        for n in colour:
            if colour[n] == 0:
                side[n] = "side A"
            else:
                side[n] = "side B"

    groups = {}
    for name in names:
        groups[name] = []
    for n in sorted(g.nodes()):
        groups[side[n]].append(n)
    left_name = names[0]
    right_name = names[1]
    if len(groups[right_name]) < len(groups[left_name]):
        left_name = names[1]
        right_name = names[0]
    left = groups[left_name]
    right = groups[right_name]

    adj = {}
    for u in left:
        adj[u] = sorted(g.undirected_neighbors(u))

    match_l = hopcroft_karp(adj, left, right)

    pairs = []
    unmatched_left = []
    for u in left:
        if match_l[u] is None:
            unmatched_left.append(u)
        else:
            pairs.append((u, match_l[u]))
    matched_right = set()
    for u, v in pairs:
        matched_right.add(v)
    unmatched_right = []
    for v in right:
        if v not in matched_right:
            unmatched_right.append(v)

    listed_pairs = []
    for u, v in pairs[:top_k]:
        listed_pairs.append({"left": node_ref(g, u), "right": node_ref(g, v)})
    listed_unmatched_left = []
    for u in unmatched_left[:top_k]:
        listed_unmatched_left.append(node_ref(g, u))
    listed_unmatched_right = []
    for v in unmatched_right[:top_k]:
        listed_unmatched_right.append(node_ref(g, v))

    result = {
        "left_side": left_name,
        "right_side": right_name,
        "left_count": len(left),
        "right_count": len(right),
        "matching_size": len(pairs),
        "pairs": listed_pairs,
        "unmatched_left": listed_unmatched_left,
        "unmatched_right": listed_unmatched_right,
    }

    summary = (f"A maximum matching has {len(pairs)} pairs between the {len(left)} '{left_name}' nodes and the "
               f"{len(right)} '{right_name}' nodes; {len(unmatched_left)} '{left_name}' and "
               f"{len(unmatched_right)} '{right_name}' nodes stay unmatched.")
    if len(pairs) == len(left) and len(pairs) == len(right):
        summary = summary + " It is a perfect matching."
    if g.directed:
        summary = summary + " Edge direction was ignored."

    while True:
        listed = len(listed_pairs) + len(listed_unmatched_left) + len(listed_unmatched_right)
        total = len(pairs) + len(unmatched_left) + len(unmatched_right)
        text = summary
        if listed < total:
            text = summary + " Lists are cut to top_k entries; the counts above are complete."
        out = ok(result, text)
        if len(json.dumps(out).encode("utf-8")) <= MAX_OUTPUT_BYTES or listed == 0:
            return out
        longest = listed_pairs
        if len(listed_unmatched_left) > len(longest):
            longest = listed_unmatched_left
        if len(listed_unmatched_right) > len(longest):
            longest = listed_unmatched_right
        longest.pop()
