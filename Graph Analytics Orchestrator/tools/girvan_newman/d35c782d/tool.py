"""Girvan-Newman communities: repeatedly removes the edge with the highest betweenness, then keeps the best split.

Rules (the validator checks them):
- Implement the algorithm yourself: standard library, NumPy and graphkit only.
- Get graphs only from the store; never open files, print, or use the network.
- Never crash: return error("what went wrong and how to fix it") instead.
- Return every node as node_ref(g, node, ...), so it has both an id and a label.
- Keep the output under 8 KB: respect top_k.
- Be deterministic: same input, same output. Randomised algorithms take a `seed` parameter (default 0).
"""
import heapq
import json
from collections import deque

from graphkit.contract import MAX_OUTPUT_BYTES, check_top_k, error, get_graph, node_ref, ok

WARN_EDGES = 600  # above this many edges the run may take more than the 30 s limit (it is still run in full)


def _edge_list(g, directed):
    """The edges to work on as [(u, v)], in the order NetworkX would list them (so ties are broken the same way).

    Undirected view: each pair once, self-loops dropped. Directed view: every arc."""
    nodes = g.nodes()
    if directed:
        return [(u, v) for u, v, _ in g.edges() if u != v]
    first = {n: {} for n in nodes}  # adjacency as NetworkX builds it from g.edges()
    for u, v, _ in g.edges():
        first[u][v] = True
        if not g.directed:
            first[v][u] = True
    adj = {n: {} for n in nodes}  # adjacency after to_undirected()
    for u in nodes:
        for v in first[u]:
            adj[u][v] = True
            adj[v][u] = True
    seen, edges = set(), []
    for u in nodes:
        for v in adj[u]:
            if v != u and v not in seen:
                edges.append((u, v))
        seen.add(u)
    return edges


def _modularity(g, partition):
    """Modularity Q of a partition (list of node lists) of the graph as it is: weighted if the graph is weighted,
    with the directed formula if the graph is directed."""
    community = {n: i for i, members in enumerate(partition) for n in members}
    total = 0.0
    inside = {}
    out_w, in_w = {}, {}
    for u, v, w in g.edges():
        total += w
        cu, cv = community[u], community[v]
        out_w[cu] = out_w.get(cu, 0.0) + w
        in_w[cv] = in_w.get(cv, 0.0) + w
        if not g.directed:  # an undirected edge counts at both ends
            out_w[cv] = out_w.get(cv, 0.0) + w
            in_w[cu] = in_w.get(cu, 0.0) + w
        if cu == cv:
            inside[cu] = inside.get(cu, 0.0) + w
    if total <= 0:
        return 0.0
    q = 0.0
    for c in range(len(partition)):
        if g.directed:
            q += inside.get(c, 0.0) / total - out_w.get(c, 0.0) * in_w.get(c, 0.0) / total ** 2
        else:
            q += inside.get(c, 0.0) / total - (out_w.get(c, 0.0) / (2 * total)) ** 2
    return q


def run(store, graph_id, n_communities=None, use_weights=False, use_direction=False, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}.")
    k, err = check_top_k(top_k)
    if err:
        return err
    # Useful Graph methods:
    #   g.nodes(), g.number_of_nodes(), g.number_of_edges(), g.directed, g.weighted
    #   g.out_neighbors(n), g.in_neighbors(n), g.undirected_neighbors(n)   -> {neighbour: weight}
    #   g.edges() -> (u, v, weight), g.weight(u, v), g.label(n), g.node_attrs(n)
    nodes = g.nodes()
    if not nodes:
        return error(f"Graph '{graph_id}' has no nodes.")
    if not isinstance(use_weights, bool) or not isinstance(use_direction, bool):
        return error("use_weights and use_direction must be true or false.")
    if n_communities is not None:
        if isinstance(n_communities, bool) or not isinstance(n_communities, int) or not 2 <= n_communities <= len(nodes):
            return error(f"n_communities must be a whole number between 2 and {len(nodes)} (the number of nodes), "
                         f"or left out to pick the split with the best modularity; got {n_communities!r}.")
    if use_weights and any(w <= 0 for _, _, w in g.edges()):
        return error("use_weights needs every edge weight to be above 0 (weights are used as distances).")

    # Step 1: the working graph. succ[u] = {neighbour: edge index}; und[u] = neighbours in either direction.
    directed = g.directed and use_direction
    edges = _edge_list(g, directed)
    length = []
    succ = {n: {} for n in nodes}
    und = {n: set() for n in nodes}
    for i, (u, v) in enumerate(edges):
        length.append(g.weight(u, v) if use_weights else 1.0)
        succ[u][v] = i
        und[u].add(v)
        und[v].add(u)
        if not directed:
            succ[v][u] = i
    alive = [True] * len(edges)
    score = [0.0] * len(edges)  # edge betweenness (both directions counted for undirected graphs, which keeps the ranking)
    order = {n: i for i, n in enumerate(nodes)}

    # Step 2: edge betweenness inside one component (Brandes): from every source count the shortest paths
    # (sigma), then work back up the search tree handing each node's credit to its parent edges.
    def betweenness(members):
        for u in members:
            for e in succ[u].values():
                score[e] = 0.0
        for s in members:
            sigma, dist, parents, stack = {s: 1.0}, {s: 0.0}, {s: []}, []
            if use_weights:
                done, heap, count = set(), [(0.0, 0, s)], 0
                while heap:
                    d, _, v = heapq.heappop(heap)
                    if v in done:
                        continue
                    done.add(v)
                    stack.append(v)
                    for w, e in succ[v].items():
                        if w in done:
                            continue
                        nd = d + length[e]
                        eps = 1e-9 * max(1.0, nd)
                        if w not in dist or nd < dist[w] - eps:
                            dist[w], sigma[w], parents[w] = nd, sigma[v], [(v, e)]
                            count += 1
                            heapq.heappush(heap, (nd, count, w))
                        elif abs(nd - dist[w]) <= eps:
                            sigma[w] += sigma[v]
                            parents[w].append((v, e))
            else:
                queue = deque([s])
                while queue:
                    v = queue.popleft()
                    stack.append(v)
                    for w, e in succ[v].items():
                        if w not in dist:
                            dist[w], sigma[w], parents[w] = dist[v] + 1, 0.0, []
                            queue.append(w)
                        if dist[w] == dist[v] + 1:
                            sigma[w] += sigma[v]
                            parents[w].append((v, e))
            delta = dict.fromkeys(stack, 0.0)
            while stack:
                w = stack.pop()
                coefficient = (1.0 + delta[w]) / sigma[w]
                for v, e in parents[w]:
                    credit = sigma[v] * coefficient
                    score[e] += credit
                    delta[v] += credit

    def reach(start):
        """All nodes connected to start (direction ignored) with the edges that are left."""
        seen, queue = {start}, deque([start])
        while queue:
            u = queue.popleft()
            for v in und[u]:
                if v not in seen:
                    seen.add(v)
                    queue.append(v)
        return seen

    # Step 3: start from the connected pieces, then split the graph one removed edge at a time.
    comp_members, comp_of, seen_nodes = {}, {}, set()
    for n in nodes:
        if n not in seen_nodes:
            part = reach(n)
            seen_nodes |= part
            cid = len(comp_members)
            comp_members[cid] = sorted(part, key=order.get)
            for x in part:
                comp_of[x] = cid
    next_id = len(comp_members)
    initial = sorted(comp_members.values(), key=lambda p: order[p[0]])
    for members in comp_members.values():
        betweenness(members)

    candidates_best = None  # (modularity, partition, removed)
    chosen = None
    removed = 0
    if not edges:
        chosen = (initial, 0)
    elif n_communities is not None and len(initial) >= n_communities:
        chosen = (initial, 0)
    while chosen is None:
        top = max(score[i] for i in range(len(edges)) if alive[i])
        tolerance = 1e-9 * max(1.0, top)
        i = next(i for i in range(len(edges)) if alive[i] and score[i] >= top - tolerance)
        u, v = edges[i]
        alive[i] = False
        removed += 1
        del succ[u][v]
        if not directed:
            del succ[v][u]
        if directed and u in succ[v]:
            pass  # the opposite arc still joins them
        else:
            und[u].discard(v)
            und[v].discard(u)
        cid = comp_of[u]
        part = reach(u)
        if v in part:
            betweenness(comp_members[cid])
        else:
            rest = [x for x in comp_members[cid] if x not in part]
            comp_members[cid] = [x for x in comp_members[cid] if x in part]
            comp_members[next_id] = rest
            for x in rest:
                comp_of[x] = next_id
            next_id += 1
            betweenness(comp_members[cid])
            betweenness(rest)
            partition = sorted((list(m) for m in comp_members.values()), key=lambda p: order[p[0]])
            if n_communities is not None:
                if len(partition) >= n_communities:
                    chosen = (partition, removed)
            else:
                q = _modularity(g, partition)
                if candidates_best is None or q > candidates_best[0] + 1e-12:
                    candidates_best = (q, partition, removed)
        if chosen is None and not any(alive):
            break
    if chosen is None:
        chosen = (candidates_best[1], candidates_best[2])
    partition, removed = chosen
    quality = _modularity(g, partition)

    # Step 4: register each listed community as a subgraph, largest first (ties by smallest node id).
    partition = sorted((sorted(p) for p in partition), key=lambda p: (-len(p), p[0]))
    listed = []
    for number, members in enumerate(partition[:k], start=1):
        sub_id = store.subgraph(graph_id, members, f"Community {number} of '{graph_id}' found by Girvan-Newman")
        listed.append((number, members, sub_id, store.get(sub_id).number_of_edges()))

    # Step 5: build the output, listing fewer members (and then fewer communities) if it would be over 8 KB.
    way = []
    if use_weights:
        way.append("weights used as distances")
    if directed:
        way.append("edge direction followed")
    how = f" ({', '.join(way)})" if way else ""
    warning = ""
    if len(edges) > WARN_EDGES:
        warning = (f" Warning: this graph has {len(edges)} connections, and Girvan-Newman recomputes edge betweenness "
                   f"after every removal, so it can take more than 30 seconds.")

    def build(shown, cap):
        result = []
        for number, members, sub_id, n_edges in listed[:shown]:
            result.append({"community": number, "graph_id": sub_id, "size": len(members), "n_edges": n_edges,
                           "nodes": [node_ref(g, n) for n in members[:cap]]})
        mode = (f"{n_communities} requested" if n_communities is not None else "best modularity")
        shown_note = ""
        if cap < len(partition[0]):
            shown_note = f", listing only the first {cap} members of each to stay under 8 KB (see size for the full count)"
        summary = (f"Girvan-Newman{how} found {len(partition)} communities ({mode}), modularity {round(quality, 6)}, "
                   f"after removing {removed} of {len(edges)} edges. The largest has {len(partition[0])} nodes"
                   f"{shown_note}.{warning}")
        return ok(result, summary, result_graph_id=listed[0][2])

    shown, cap = len(listed), len(partition[0])
    out = build(shown, cap)
    while (shown > 1 or cap > 1) and len(json.dumps(out, sort_keys=True).encode("utf-8")) > MAX_OUTPUT_BYTES - 500:
        if cap > 1:
            cap = max(1, cap - max(1, cap // 5))
        else:
            shown -= 1
        out = build(shown, cap)
    return out

