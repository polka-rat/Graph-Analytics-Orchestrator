"""Local clustering coefficient of nodes, and the graph's average clustering.

Rules (the validator checks them):
- Implement the algorithm yourself: standard library, NumPy and graphkit only.
- Get graphs only from the store; never open files, print, or use the network.
- Never crash: return error("what went wrong and how to fix it") instead.
- Return every node as node_ref(g, node, ...), so it has both an id and a label.
- Keep the output under 8 KB: respect top_k.
- Be deterministic: same input, same output. Randomised algorithms take a `seed` parameter (default 0).
"""
import json

from graphkit.contract import MAX_OUTPUT_BYTES, check_node, check_top_k, error, get_graph, node_ref, ok


def _undirected_clustering(g):
    """{node: (clustering, degree)} for an undirected graph.

    For a node with d neighbours, d*(d-1)/2 pairs of neighbours are possible;
    clustering = (pairs that are joined by an edge) / (possible pairs).
    """
    nbrs = {v: set(g.neighbors(v)) - {v} for v in g.nodes()}
    out = {}
    for v, vs in nbrs.items():
        d = len(vs)
        # Each linked pair (u, w) is seen twice: once from u and once from w.
        twice_links = sum(len(vs & nbrs[u]) for u in vs)
        out[v] = (twice_links / (d * (d - 1)) if twice_links else 0.0, d)
    return out


def _directed_clustering(g):
    """{node: (clustering, total degree)} for a directed graph.

    Uses the directed definition (Fagiolo, 2007), the one NetworkX uses:
    clustering = T / (2 * (d_tot * (d_tot - 1) - 2 * d_both)), where T counts the
    directed triangles through the node, d_tot = in-degree + out-degree and
    d_both = number of neighbours joined to the node in both directions.
    """
    preds = {v: set(g.in_neighbors(v)) - {v} for v in g.nodes()}
    succs = {v: set(g.out_neighbors(v)) - {v} for v in g.nodes()}
    out = {}
    for v in g.nodes():
        vp, vs = preds[v], succs[v]
        triangles = 0
        # A neighbour joined in both directions is visited twice, as in the definition.
        for u in list(vp) + list(vs):
            up, us = preds[u], succs[u]
            triangles += len(vp & up) + len(vp & us) + len(vs & up) + len(vs & us)
        d_tot = len(vp) + len(vs)
        d_both = len(vp & vs)
        out[v] = (triangles / (2 * (d_tot * (d_tot - 1) - 2 * d_both)) if triangles else 0.0, d_tot)
    return out


def run(store, graph_id, node=None, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     f"clustering_coefficient takes graph_id, node and top_k.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if node is not None:
        err = check_node(g, node)
        if err:
            return err
    n = g.number_of_nodes()
    if n == 0:
        return error(f"Graph '{graph_id}' has no nodes, so it has no clustering coefficient. "
                     f"Use list_graphs to pick another graph.")

    scores = _directed_clustering(g) if g.directed else _undirected_clustering(g)
    average = round(sum(c for c, _ in scores.values()) / n, 6)

    if node is not None:
        c, d = scores[node]
        entry = node_ref(g, node, clustering=round(c, 6), degree=d)
        summary = (f"{entry['label']} ({node}) has clustering coefficient {entry['clustering']} "
                   f"(1 means all its neighbours are linked to each other, 0 means none are). "
                   f"The average over all {n} nodes of '{graph_id}' is {average}.")
        return ok({"node": entry, "average_clustering": average}, summary)

    # Highest clustering first; ties broken by node id so the output is deterministic.
    top = sorted(scores.items(), key=lambda item: (-round(item[1][0], 6), item[0]))[:k]
    nodes = [node_ref(g, v, clustering=round(c, 6), degree=d) for v, (c, d) in top]
    best = nodes[0]
    if best["clustering"] == 0:
        summary = (f"Every node of '{graph_id}' has clustering coefficient 0: no node has two neighbours "
                   f"that are linked to each other (the graph has no triangles).")
    else:
        summary = (f"The average clustering coefficient of '{graph_id}' is {average} over {n} nodes. "
                   f"The most clustered node is {best['label']} ({best['id']}) with {best['clustering']}.")
    out = ok({"average_clustering": average, "top_nodes": nodes}, summary)

    # Long labels (e.g. airport names) can push top_k=100 over the 8 KB limit: return fewer nodes.
    while len(json.dumps(out, sort_keys=True).encode("utf-8")) > MAX_OUTPUT_BYTES - 200:
        nodes.pop()
        out = ok({"average_clustering": average, "top_nodes": nodes},
                 f"{summary} Only the top {len(nodes)} nodes are listed, to keep the output under 8 KB.")
    return out
