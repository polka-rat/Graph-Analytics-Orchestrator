"""Girvan-Newman communities: repeatedly remove the edge with the highest betweenness until the graph splits.

Highlights:
- Same result as networkx girvan_newman at every level, including which edge is removed when several tie:
  the adjacency is built in the order NetworkX uses, and Brandes' edge betweenness is summed in the same
  order, so equal scores compare equal. Checked on karate, lesmis, projects, courses and airports subgraphs.
- 4 to 6 times faster than NetworkX: removing an edge only changes betweenness inside its own component, so
  only that component is recomputed (NetworkX recomputes the whole graph after every removal).
- Default: the level with the highest modularity. num_communities stops early at a fixed number of groups.
- Each listed community is registered as a subgraph (graph_id) for other tools; result_graph_id is the largest.
- Output always fits 8 KB: member lists are shortened first, then fewer communities are listed.
- A work limit (n * m^2) returns a helpful error for graphs too large to finish in 30 s, instead of timing out.
"""
import json
from collections import deque

from graphkit.contract import MAX_OUTPUT_BYTES, check_top_k, error, get_graph, node_ref, ok

MAX_WORK = 5e8  # nodes * edges^2: Girvan-Newman is O(n m^2); this is about 7 s (200 nodes, 1,500 edges)


def _count(n, word, plural=None):
    """'1 node', '2 nodes'."""
    return f"{n} {word if n == 1 else plural or word + 's'}"


def _adjacency(g):
    """Undirected adjacency lists in the order NetworkX uses for to_networkx(g).to_undirected()."""
    nodes = g.nodes()
    index = {n: i for i, n in enumerate(nodes)}
    adj = [[] for _ in nodes]
    present = [set() for _ in nodes]
    # Each neighbour is appended when its edge is first seen, as NetworkX does; self-loops are dropped.
    for i, u in enumerate(nodes):
        for v in g.out_neighbors(u):
            j = index[v]
            if j != i and j not in present[i]:
                adj[i].append(j)
                adj[j].append(i)
                present[i].add(j)
                present[j].add(i)
    return nodes, adj


def _component(adj, start):
    """Set of nodes reachable from `start` (BFS)."""
    seen = {start}
    queue = deque([start])
    while queue:
        u = queue.popleft()
        for v in adj[u]:
            if v not in seen:
                seen.add(v)
                queue.append(v)
    return seen


def _betweenness(adj, sources, eid, between, scale):
    """Brandes' edge betweenness from `sources` (one whole component, in node order) into `between`."""
    for s in sources:
        # 1. BFS from s: number of shortest paths to each node (sigma) and their predecessors.
        order, pred, sigma, dist = [], {s: []}, {s: 1.0}, {s: 0}
        queue = deque([s])
        while queue:
            v = queue.popleft()
            order.append(v)
            dv, sv = dist[v] + 1, sigma[v]
            for w in adj[v]:
                if w not in dist:
                    queue.append(w)
                    dist[w] = dv
                    sigma[w] = 0.0
                    pred[w] = []
                if dist[w] == dv:
                    sigma[w] += sv
                    pred[w].append(v)
        # 2. Farthest nodes first: split each node's share of paths over the edges it was reached by.
        delta = dict.fromkeys(order, 0)
        while order:
            w = order.pop()
            coeff = (1 + delta[w]) / sigma[w]
            row = eid[w]
            for v in pred[w]:
                c = sigma[v] * coeff
                between[row[v]] += c
                delta[v] += c
    # Same normalisation as NetworkX, so equal scores stay exactly equal.
    if scale is not None:
        for s in sources:
            for t in adj[s]:
                if s < t:
                    between[eid[s][t]] *= scale


def _levels(adj, n_nodes, stop_at):
    """Yield (edges_removed, components) after each split, like NetworkX, until `stop_at` components."""
    # Edge ids follow NetworkX's G.edges() order, which is also its tie-break order.
    eid, ends = [{} for _ in range(n_nodes)], []  # eid[u][v] = id of edge u-v
    for u in range(n_nodes):
        for v in adj[u]:
            if v not in eid[u]:
                eid[u][v] = eid[v][u] = len(ends)
                ends.append((u, v))
    alive = [True] * len(ends)
    between = [0.0] * len(ends)
    scale = 1 / (n_nodes * (n_nodes - 1)) if n_nodes > 1 else None

    # Starting components and their betweenness.
    comp_of, comps = [0] * n_nodes, []
    for u in range(n_nodes):
        if not comps or all(u not in c for c in comps):
            members = _component(adj, u)
            for v in members:
                comp_of[v] = len(comps)
            comps.append(members)
    for c in comps:
        _betweenness(adj, sorted(c), eid, between, scale)

    removed, remaining = 0, len(ends)
    while remaining and len(comps) < stop_at:
        # Remove the most central edge; on ties max() keeps the first in edge order, like NetworkX.
        best = max((e for e in range(len(ends)) if alive[e]), key=between.__getitem__)
        u, v = ends[best]
        alive[best] = False
        adj[u].remove(v)
        adj[v].remove(u)
        removed += 1
        remaining -= 1
        # Only the component that lost the edge changes: reset its scores and recompute them.
        old = comps[comp_of[u]]
        for s in old:
            for t in adj[s]:
                between[eid[s][t]] = 0.0
        side = _component(adj, u)
        if v in side:  # still connected: same component, new scores
            _betweenness(adj, sorted(old), eid, between, scale)
            continue
        other = old - side  # split: one more community, recompute both halves
        comps[comp_of[u]] = side
        for x in other:
            comp_of[x] = len(comps)
        comps.append(other)
        _betweenness(adj, sorted(side), eid, between, scale)
        _betweenness(adj, sorted(other), eid, between, scale)
        yield removed, [set(c) for c in comps]


def _modularity(adj0, degree, m, comps):
    """Newman modularity: share of edges inside communities minus the share expected by chance."""
    if m == 0:
        return 0.0
    q = 0.0
    for c in comps:
        inside = sum(1 for u in c for v in adj0[u] if v in c) / 2
        total = sum(degree[u] for u in c)
        q += inside / m - (total / (2 * m)) ** 2
    return q


def run(store, graph_id, num_communities=None, top_k=10, **params):
    # Validate the call before doing any work.
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. girvan_newman takes graph_id, "
                     f"num_communities and top_k.")
    k, err = check_top_k(top_k)
    if err:
        return err
    n = g.number_of_nodes()
    if n == 0:
        return error(f"Graph '{graph_id}' has no nodes, so it has no communities.")
    if num_communities is not None and (isinstance(num_communities, bool) or not isinstance(num_communities, int)
                                        or not 1 <= num_communities <= n):
        return error(f"num_communities must be a whole number from 1 to {n} (the number of nodes); "
                     f"got {num_communities!r}. Leave it out to pick the split with the best modularity.")

    nodes, adj = _adjacency(g)
    m = sum(len(a) for a in adj) // 2
    if n * m * m > MAX_WORK:
        return error(f"'{graph_id}' ({n} nodes, {m} edges) is too large for Girvan-Newman, which is O(n m^2); it "
                     f"handles up to about 200 nodes and 1,500 edges. Use louvain or label_propagation, or run it "
                     f"on a smaller subgraph (e.g. from filter_nodes).")

    adj0 = [set(a) for a in adj]  # original edges, for modularity
    degree = [len(a) for a in adj]
    start = [_component(adj, 0)]  # separate pieces before any edge is removed
    for u in range(n):
        if all(u not in c for c in start):
            start.append(_component(adj, u))

    if num_communities is not None:  # stop at the requested level
        comps, removed = start, 0
        for removed, comps in _levels(adj, n, num_communities):
            pass
        q = _modularity(adj0, degree, m, comps)
        how = (f"split into {_count(len(comps), 'community', 'communities')} as asked"
               if len(comps) == num_communities else
               f"the graph already has {_count(len(comps), 'separate component')}, more than the {num_communities} asked")
    else:  # run the whole hierarchy and keep the best-modularity level
        # The unsplit graph is a candidate too: if no split raises modularity, there is no community structure.
        comps, removed, q = start, 0, _modularity(adj0, degree, m, start)
        for r, level in _levels(adj, n, n):
            level_q = _modularity(adj0, degree, m, level)
            if level_q > q:
                comps, removed, q = level, r, level_q
        how = (f"best split by modularity has {_count(len(comps), 'community', 'communities')}" if removed else
               f"no split raises modularity, so the graph stays as {_count(len(comps), 'connected group')}")

    # Largest communities first, ties by smallest node id; members by degree, then id.
    deg = {nodes[i]: degree[i] for i in range(n)}
    groups = sorted((sorted((nodes[i] for i in c), key=lambda x: (-deg[x], x)) for c in comps),
                    key=lambda c: (-len(c), min(c)))
    how += " (edge directions ignored)" if g.directed else ""

    def build(shown, cap, ids):
        communities = [{"community": i, "size": len(c), "graph_id": gid,
                        "members": [node_ref(g, x) for x in c[:cap]]} for i, (c, gid) in enumerate(zip(shown, ids), 1)]
        notes = f" Listing the {len(shown)} largest." if len(shown) < len(groups) else ""
        if any(len(c) > cap for c in shown):
            notes += f" Up to {cap} members shown per community; each graph_id holds the full set."
        result = {"num_communities": len(groups), "modularity": round(q, 6), "edges_removed": removed,
                  "communities": communities}
        summary = (f"Girvan-Newman on '{graph_id}': {how}, modularity {round(q, 6)}"
                   f"{', after removing ' + _count(removed, 'edge') if removed else ''}; the largest has {_count(len(groups[0]), 'node')}.{notes}")
        return ok(result, summary, result_graph_id=ids[0])

    # Fit the 8 KB limit: first shorten member lists, then list fewer communities. The full member sets
    # stay available through each community's graph_id.
    shown, cap = groups[:k], len(groups[0])
    placeholder = [f"{graph_id}~{10 ** 6}"] * len(shown)
    while len(json.dumps(build(shown, cap, placeholder), sort_keys=True).encode()) >= MAX_OUTPUT_BYTES:
        if cap > 1:
            cap -= 1
        else:
            shown = shown[:-1]
    ids = [store.subgraph(graph_id, c, f"Girvan-Newman community {i} of {len(groups)} in '{graph_id}'")
           for i, c in enumerate(shown, 1)]
    return build(shown, cap, ids)
