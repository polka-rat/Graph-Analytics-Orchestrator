"""Core number of every node (Batagelj-Zaversnik bucket algorithm) and the k-core subgraph.

The k-core is the largest subgraph in which every node has at least k neighbours inside it.
A node's core number is the largest k for which it belongs to the k-core. Directed graphs are
treated as undirected (edge direction is ignored); weights are ignored; self-loops are skipped.
"""
from graphkit.contract import check_node, check_top_k, error, get_graph, node_ref, ok


def core_numbers(g):
    """{node: core number}, peeling nodes in order of current degree in O(n + m)."""
    nbrs = {v: set(g.undirected_neighbors(v)) - {v} for v in g.nodes()}
    deg = {v: len(nb) for v, nb in nbrs.items()}
    max_deg = max(deg.values(), default=0)
    buckets = [[] for _ in range(max_deg + 1)]
    for v in sorted(deg):  # sorted so the peeling order is deterministic
        buckets[deg[v]].append(v)
    core, removed = {}, set()
    k = 0
    for d in range(max_deg + 1):
        k = max(k, d)
        while buckets[d]:
            v = buckets[d].pop()
            if v in removed or deg[v] != d:
                continue  # stale bucket entry
            removed.add(v)
            core[v] = k
            for u in nbrs[v]:
                if u not in removed and deg[u] > d:
                    deg[u] -= 1
                    buckets[max(deg[u], d)].append(u)
            # a neighbour may have dropped into bucket d: the while loop picks it up
    return core


def run(store, graph_id, k=None, node=None, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. k_core takes graph_id, k, node and top_k.")
    t, err = check_top_k(top_k)
    if err:
        return err
    if k is not None and (isinstance(k, bool) or not isinstance(k, int) or k < 0):
        return error(f"k must be a whole number >= 0; got {k!r}. Omit k to get the densest (maximum) core.")
    if node is not None:
        err = check_node(g, node)
        if err:
            return err
    if g.number_of_nodes() == 0:
        return error(f"Graph '{graph_id}' has no nodes. Pick another graph.")

    core = core_numbers(g)
    max_core = max(core.values())
    if k is None:
        k = max_core
    if k > max_core:
        return error(f"The {k}-core of '{graph_id}' is empty: the largest core number is {max_core}. "
                     f"Use k <= {max_core}, or omit k to get the densest core.")

    members = sorted((v for v in core if core[v] >= k), key=lambda v: (-core[v], v))
    sub_id = store.subgraph(graph_id, members, f"{k}-core of '{graph_id}' ({len(members)} nodes)")
    distribution = {}
    for c in core.values():
        distribution[c] = distribution.get(c, 0) + 1
    note = " Edge direction was ignored." if g.directed else ""

    result = {
        "k": k,
        "max_core": max_core,
        "core_size": len(members),
        "core_edges": store.get(sub_id).number_of_edges(),
        "core_number_counts": [{"core_number": c, "nodes": distribution[c]} for c in sorted(distribution)],
        "members": [node_ref(g, v, core_number=core[v]) for v in members[:t]],
    }
    summary = (f"The {k}-core of '{graph_id}' has {len(members)} of {g.number_of_nodes()} nodes "
               f"(each with at least {k} neighbours inside it); the maximum core number is {max_core}. "
               f"The core is returned as a subgraph in result_graph_id.{note}")
    if node is not None:
        result["node"] = node_ref(g, node, core_number=core[node], in_core=core[node] >= k)
        summary = f"{g.label(node)} has core number {core[node]}. " + summary
    return ok(result, summary, result_graph_id=sub_id)
