"""Clustering coefficient: how closely a node's neighbours are connected to each other.

Rules (the validator checks them):
- Standard library, NumPy and graphkit only; graphs come from the store only.
- Never crashes: bad input returns error(...).
"""
import json

from graphkit.contract import MAX_OUTPUT_BYTES, check_node, check_top_k, error, get_graph, node_ref, ok

# Leave headroom below the 8 KB limit for the summary and the JSON envelope.
_RESULT_BUDGET = MAX_OUTPUT_BYTES - 1500


def _undirected_coefficient(adj, v):
    """C(v) = 2 * (links among v's neighbours) / (k * (k - 1)); 0 when k < 2."""
    nbrs = adj[v]
    k = len(nbrs)
    if k < 2:
        return 0.0, k
    # Each link between two neighbours is seen from both ends, hence the // 2.
    links = sum(len(adj[a] & nbrs) for a in nbrs) // 2
    return 2.0 * links / (k * (k - 1)), k


def _directed_coefficient(out, inn, v):
    """Directed clustering of Fagiolo (2007), the definition NetworkX uses for DiGraphs.

    s(x, y) = number of edges between x and y (0, 1 or 2: one per direction).
    C(v) = sum over ordered neighbour pairs (j, h) of s(v,j) * s(j,h) * s(h,v)
           / (2 * (d_tot * (d_tot - 1) - 2 * d_bidirectional))
    """
    o, i = out[v], inn[v]
    d_tot = len(o) + len(i)
    d_bi = len(o & i)
    denom = 2 * (d_tot * (d_tot - 1) - 2 * d_bi)
    if denom <= 0:
        return 0.0, d_tot
    nbrs = o | i
    total = 0
    for j in nbrs:
        s_vj = (j in o) + (j in i)
        for h in (out[j] | inn[j]) & nbrs:
            total += s_vj * ((h in out[j]) + (h in inn[j])) * ((h in o) + (h in i))
    return total / denom, d_tot


def run(store, graph_id, node=None, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     "clustering_coefficient takes graph_id, node (optional) and top_k (optional).")
    k, err = check_top_k(top_k)
    if err:
        return err
    if node is not None:
        err = check_node(g, node)
        if err:
            return err

    nodes = g.nodes()
    if not nodes:
        return error(f"Graph '{graph_id}' has no nodes, so there is nothing to compute.")

    # A node is never its own neighbour: remove self-loops from every neighbour set.
    if g.directed:
        out = {n: set(g.out_neighbors(n)) - {n} for n in nodes}
        inn = {n: set(g.in_neighbors(n)) - {n} for n in nodes}
        calc = lambda n: _directed_coefficient(out, inn, n)  # noqa: E731
    else:
        adj = {n: set(g.neighbors(n)) - {n} for n in nodes}
        calc = lambda n: _undirected_coefficient(adj, n)  # noqa: E731

    values = {n: calc(n) for n in nodes}
    average = sum(c for c, _ in values.values()) / len(nodes)
    kind = "directed (Fagiolo)" if g.directed else "undirected"

    if node is not None:
        c, deg = values[node]
        entries = [node_ref(g, node, clustering=round(c, 6), degree=deg)]
        summary = (f"The clustering coefficient of {g.label(node)} ({node}) in '{graph_id}' is {round(c, 6)} "
                   f"({kind}, degree {deg}); the graph average is {round(average, 6)}.")
    else:
        ranked = sorted(values.items(), key=lambda item: (-item[1][0], item[0]))[:k]
        entries = [node_ref(g, n, clustering=round(c, 6), degree=deg) for n, (c, deg) in ranked]
        # Stay under the 8 KB limit even when top_k is large: drop the lowest-ranked entries.
        while len(entries) > 1 and len(json.dumps(entries)) > _RESULT_BUDGET:
            entries.pop()
        best = entries[0]
        summary = (f"Average clustering coefficient of '{graph_id}' is {round(average, 6)} ({kind}). "
                   f"Highest of {len(nodes)} nodes: {best['label']} ({best['id']}) with {best['clustering']}.")
        if len(entries) < k and len(entries) < len(nodes):
            summary += f" Showing {len(entries)} nodes (output size limit)."

    return ok({"average_clustering": round(average, 6), "graph_type": kind, "nodes": entries}, summary)
