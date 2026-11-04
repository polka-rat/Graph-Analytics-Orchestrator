"""k_core: the core number of every node, and the nodes of one k-core.

Author: b2d75536. Medium tier, community category.

The k-core is the largest subgraph in which every node has at least k neighbours
*inside* the subgraph. A node's core number is the largest k whose core contains
it. Both come from one peeling pass: repeatedly remove the node of smallest
current degree, and record the degree it had when it was removed.

The peeling uses a heap, so it runs in O(E log V) on an unweighted graph. On a
directed graph degree means in-degree + out-degree, the usual convention, so a
pair joined in both directions counts twice.
"""
import heapq
import json

from graphkit.contract import MAX_OUTPUT_BYTES, check_top_k, error, get_graph, node_ref, ok


def _adjacency(g):
    """{node: {neighbour: how many edges join them}}, ignoring direction."""
    adj = {n: {} for n in g.nodes()}
    for u, v, _ in g.edges():
        if u == v:
            continue  # a self-loop adds no neighbour, so it cannot keep a node in a core
        adj[u][v] = adj[u].get(v, 0) + 1
        adj[v][u] = adj[v].get(u, 0) + 1
    return adj


def _core_numbers(adj):
    """Core number of every node, by peeling the smallest-degree node first."""
    degree = {n: sum(nbrs.values()) for n, nbrs in adj.items()}
    heap = [(d, n) for n, d in degree.items()]
    heapq.heapify(heap)
    core, removed, level = {}, set(), 0
    while heap:
        d, n = heapq.heappop(heap)
        if n in removed or d != degree[n]:
            continue  # a stale entry: this node's degree has dropped since it was pushed
        level = max(level, d)
        core[n] = level
        removed.add(n)
        for v, times in adj[n].items():
            if v not in removed:
                degree[v] -= times
                heapq.heappush(heap, (degree[v], v))
    return core


def _fits(result, summary, result_graph_id):
    """True if this output stays inside the 8 KB the contract allows."""
    text = json.dumps(ok(result, summary, result_graph_id), allow_nan=False, sort_keys=True)
    return len(text.encode("utf-8")) <= MAX_OUTPUT_BYTES


def run(store, graph_id, k=None, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. k_core takes graph_id, k and top_k.")
    if k is not None and (isinstance(k, bool) or not isinstance(k, int) or k < 0):
        return error(f"k must be a whole number of 0 or more, or left out for the densest core; got {k!r}.")
    limit, err = check_top_k(top_k)
    if err:
        return err
    if g.number_of_nodes() == 0:
        return error(f"Graph '{graph_id}' has no nodes, so it has no cores.")

    adj = _adjacency(g)
    core = _core_numbers(adj)
    max_core = max(core.values())
    wanted = max_core if k is None else k

    counts = {}
    for value in core.values():
        counts[value] = counts.get(value, 0) + 1
    distribution = [{"k": value, "nodes": counts[value]} for value in sorted(counts)]

    members = sorted((n for n, c in core.items() if c >= wanted), key=lambda n: (-core[n], n))
    if not members:
        return ok({"k": wanted, "max_core": max_core, "core_size": 0, "core_edges": 0,
                   "core_distribution": distribution, "members_shown": 0, "members": [], "graph_id": None},
                  f"Graph '{graph_id}' has no {wanted}-core: its densest core is the {max_core}-core, "
                  f"with {counts[max_core]} nodes. Ask for k of {max_core} or less.")

    sub_id = store.subgraph(graph_id, members, f"The {wanted}-core of '{graph_id}'")
    sub = store.get(sub_id)
    listed = [node_ref(g, n, core_number=core[n], links_inside=len(sub.undirected_neighbors(n)))
              for n in members[:limit]]

    result = {
        "k": wanted,
        "max_core": max_core,
        "core_size": len(members),
        "core_edges": sub.number_of_edges(),
        "core_distribution": distribution,
        "members_shown": len(listed),
        "members": listed,
        "graph_id": sub_id,
    }
    which = "densest core (the highest k with a non-empty core)" if k is None else f"{wanted}-core"
    summary = (f"The {which} of '{graph_id}' is the {wanted}-core: {len(members)} of "
               f"{g.number_of_nodes()} nodes, each joined to at least {wanted} other members, with "
               f"{sub.number_of_edges()} edges among them. It is registered as graph '{sub_id}'.")

    # Keep the response inside 8 KB: shorten the listing, then the distribution, before giving up detail.
    while result["members"] and not _fits(result, summary, sub_id):
        result["members"].pop()
        result["members_shown"] = len(result["members"])
    while len(result["core_distribution"]) > 1 and not _fits(result, summary, sub_id):
        result["core_distribution"].pop()
    return ok(result, summary, result_graph_id=sub_id)
