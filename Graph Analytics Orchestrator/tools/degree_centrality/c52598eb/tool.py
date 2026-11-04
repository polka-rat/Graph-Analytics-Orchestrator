"""Degree centrality: ranks nodes by how many direct connections they have.

Score = degree / (n - 1), the same normalisation as NetworkX:
  - undirected graph: number of neighbours
  - directed graph:   in + out (direction="total"), in only ("in") or out only ("out")
Edge weights are ignored (degree counts edges, not distances). O(n + m) time.
"""
import json

from graphkit.contract import MAX_OUTPUT_BYTES, check_top_k, error, get_graph, node_ref, ok

DIRECTIONS = ("total", "in", "out")


def _fits(out):
    """True if the response stays under the contract's 8 KB limit."""
    return len(json.dumps(out, sort_keys=True).encode("utf-8")) <= MAX_OUTPUT_BYTES


def run(store, graph_id, top_k=10, direction="total", **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     f"degree_centrality takes graph_id, top_k and direction.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if direction not in DIRECTIONS:
        return error(f"direction must be one of 'total', 'in' or 'out'; got {direction!r}.")

    n = g.number_of_nodes()
    if n == 0:
        return error(f"Graph '{graph_id}' has no nodes, so there is nothing to rank.")
    norm = 1.0 / (n - 1) if n > 1 else 0.0  # a single node has centrality 0 (as in NetworkX)

    # Count degrees once: O(n + m).
    rows = {}
    for node in g.nodes():
        if g.directed:
            d_in, d_out = len(g.in_neighbors(node)), len(g.out_neighbors(node))
            deg = {"total": d_in + d_out, "in": d_in, "out": d_out}[direction]
            rows[node] = (deg, d_in, d_out)
        else:
            deg = len(g.out_neighbors(node))  # for undirected graphs: all neighbours
            rows[node] = (deg, None, None)

    # Sort by score, ties broken by node id (ascending) so the output is deterministic.
    ranked = sorted(rows, key=lambda u: (-round(rows[u][0] * norm, 6), u))[:k]

    def entry(u, rich):
        deg, d_in, d_out = rows[u]
        extra = {"score": round(deg * norm, 6)}
        if rich:
            extra["degree"] = deg
            if g.directed:
                extra["in_degree"], extra["out_degree"] = d_in, d_out
        return node_ref(g, u, **extra)

    best = ranked[0]
    if g.directed:
        what = {"total": "incoming plus outgoing", "in": "incoming", "out": "outgoing"}[direction]
        summary = (f"{g.label(best)} ({best}) is the most connected of {n} nodes with "
                   f"{rows[best][0]} {what} edges (degree centrality {round(rows[best][0] * norm, 6)}).")
    else:
        summary = (f"{g.label(best)} ({best}) is the most connected of {n} nodes with "
                   f"{rows[best][0]} neighbours (degree centrality {round(rows[best][0] * norm, 6)}).")

    # Keep the response under 8 KB: drop the raw counts first, then trailing entries.
    for rich in (True, False):
        out = ok([entry(u, rich) for u in ranked], summary)
        if _fits(out):
            return out
    shown = len(ranked)
    while shown > 1 and not _fits(out):
        shown -= 1
        out = ok([entry(u, False) for u in ranked[:shown]],
                 summary + f" Showing the top {shown} of {len(ranked)} requested to stay under 8 KB.")
    return out
