"""Core number of every node by k-core peeling, and the k-core (by default the densest core) as a subgraph.

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

def neighbours_per_edge(g, v):
    # directed: a node joined both ways appears twice, matching degree = in + out
    if g.directed:
        return list(g.out_neighbors(v)) + list(g.in_neighbors(v))
    return list(g.neighbors(v))

def run(store, graph_id, k=None, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}.")
    top_k, err = check_top_k(top_k)
    if err:
        return err
    if k is not None:
        if isinstance(k, bool) or not isinstance(k, int) or k < 0:
            return error(f"k must be a whole number of at least 0; got {k!r}. Leave k out to get the densest core.")
    if g.number_of_nodes() == 0:
        return error(f"Graph '{graph_id}' has no nodes, so it has no cores.")

    degree = {}
    for each in g.nodes():
        degree[each] = len(neighbours_per_edge(g, each))

    # removing level by level
    core = {}
    removed = set()
    level = 1
    while len(removed) < g.number_of_nodes():
        q = deque()
        for n in g.nodes():
            if n not in removed and degree[n] < level:
                q.append(n)
        while q:
            v = q.popleft()
            if v in removed:
                continue
            removed.add(v)
            core[v] = level - 1
            for u in neighbours_per_edge(g, v):
                if u not in removed:
                    degree[u] = degree[u] - 1
                    if degree[u] < level:
                        q.append(u)
        level = level + 1

    max_core = max(core.values())
    if k is None:
        k = max_core
    if k > max_core:
        return error(f"There is no {k}-core: the densest core of '{graph_id}' is the {max_core}-core. "
                     f"Use k from 0 to {max_core}, or leave k out.")

    core_nodes = []
    for n in g.nodes():
        if core[n] >= k:
            core_nodes.append(n)
    core_nodes.sort()
    sub_id = store.subgraph(graph_id, core_nodes, f"{k}-core of '{graph_id}' ({len(core_nodes)} nodes)")

    # highest core number first, ties by node id
    pairs = []
    for n in core_nodes:
        pairs.append((-core[n], n))
    pairs.sort()
    nodes = []
    for c, n in pairs[:top_k]:
        nodes.append(node_ref(g, n, core_number=-c))

    result = {
        "k": k,
        "max_core_number": max_core,
        "size": len(core_nodes),
        "nodes": nodes,
    }

    links = "neighbours"
    if g.directed:
        links = "connections (incoming + outgoing)"

    while True:
        summary = (f"The {k}-core of '{graph_id}' has {len(core_nodes)} nodes, each with at least {k} {links} "
                   f"inside it; the densest core is the {max_core}-core. ")
        if len(nodes) == len(core_nodes):
            summary = summary + "All are listed with their core numbers."
        else:
            summary = (summary + f"The {len(nodes)} with the highest core numbers are listed; "
                       f"the full core is in result_graph_id.")
        out = ok(result, summary, result_graph_id=sub_id)
        if len(json.dumps(out).encode("utf-8")) <= MAX_OUTPUT_BYTES or len(nodes) == 0:
            return out
        nodes.pop()
