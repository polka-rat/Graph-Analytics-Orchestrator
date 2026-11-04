"""Local clustering coefficient of each node, and the graph's average clustering.

A node's clustering is the fraction of pairs of its neighbours that are linked to each other:
2T / (d(d-1)) for T triangles through a node of degree d. Directed graphs use the directed
version (Fagiolo 2007, as NetworkX): T / (d_tot(d_tot-1) - 2 d_bi), counting every directed
triangle. With weighted=true each triangle counts as the geometric mean of its edge weights,
scaled by the largest weight (Onnela et al. 2005, as NetworkX). Self-loops are ignored.
"""
import json
import math

from graphkit.contract import (DEFAULT_TOP_K, MAX_OUTPUT_BYTES, check_node, check_top_k, error, get_graph,
                               node_ref, ok)

OUTPUT_BUDGET = MAX_OUTPUT_BYTES - 64  # stay safely under the 8 KB limit


def _as_top_k(value):
    """Accept what LLMs send for a count: null (use the default), 5.0 or "5"."""
    if value is None:
        return DEFAULT_TOP_K
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value)
    return value


def _as_node(g, value):
    """Null or "" means no node; 5 means node '5'; case and stray spaces are ignored if one node matches."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, int) and not isinstance(value, bool):
        value = str(value)
    if isinstance(value, str) and not g.has_node(value):
        matches = [n for n in g.nodes() if n.lower() == value.strip().lower()]
        if len(matches) == 1:
            return matches[0]
    return value


def _as_bool(value, default):
    """Accept null (use the default) and "true"/"false" as text."""
    if value is None:
        return default
    if isinstance(value, str) and value.strip().lower() in ("true", "false"):
        return value.strip().lower() == "true"
    return value


def _plural(n, word):
    return f"{n:,} {word}" + ("" if n == 1 else "s")


def _undirected(g, weighted):
    """{node: (clustering, degree, triangles)}; triangles is None when weighted."""
    nbrs = {u: set(g.neighbors(u)) - {u} for u in g.nodes()}
    # Scale by the largest weight; if every weight is 0, keep them 0 rather than divide by 0.
    top = (max((w for _, _, w in g.edges()), default=0.0) or 1.0) if weighted else 1.0
    out = {}
    for i in g.nodes():
        d = len(nbrs[i])
        if not weighted:
            t = sum(len(nbrs[i] & nbrs[j]) for j in nbrs[i])  # every triangle counted twice
            out[i] = (0.0 if t == 0 else t / (d * (d - 1)), d, t // 2)
            continue
        t, seen = 0.0, set()
        for j in nbrs[i]:
            seen.add(j)  # count each triangle once here, then double it
            wij = g.weight(i, j) / top
            t += sum((wij * g.weight(j, k) / top * g.weight(k, i) / top) ** (1 / 3)
                     for k in nbrs[i] & (nbrs[j] - seen))
        out[i] = (0.0 if t == 0 else 2 * t / (d * (d - 1)), d, None)
    return out


def _directed(g, weighted):
    """{node: (clustering, total degree, directed triangles)}; triangles is None when weighted."""
    preds = {u: set(g.in_neighbors(u)) - {u} for u in g.nodes()}
    succs = {u: set(g.out_neighbors(u)) - {u} for u in g.nodes()}
    # Scale by the largest weight; if every weight is 0, keep them 0 rather than divide by 0.
    top = (max((w for _, _, w in g.edges()), default=0.0) or 1.0) if weighted else 1.0

    def wt(u, v):
        return g.weight(u, v) / top

    def tri(a, b, c):
        return (a * b * c) ** (1 / 3)

    out = {}
    for i in g.nodes():
        ip, isu = preds[i], succs[i]
        t = 0
        # j is a neighbour of i, reached by the edge j->i (j in ip) or i->j (j in isu); a node
        # linked both ways is visited twice. Each k closing a triangle with i and j counts once
        # per orientation of its two edges.
        for j_list, w_ij in ((ip, lambda j: wt(j, i)), (isu, lambda j: wt(i, j))):
            for j in j_list:
                if not weighted:
                    t += len(ip & preds[j]) + len(ip & succs[j]) + len(isu & preds[j]) + len(isu & succs[j])
                    continue
                w1 = w_ij(j)
                t += sum(tri(w1, wt(k, i), wt(k, j)) for k in ip & preds[j])
                t += sum(tri(w1, wt(k, i), wt(j, k)) for k in ip & succs[j])
                t += sum(tri(w1, wt(i, k), wt(k, j)) for k in isu & preds[j])
                t += sum(tri(w1, wt(i, k), wt(j, k)) for k in isu & succs[j])
        dt = len(ip) + len(isu)
        db = len(ip & isu)
        c = 0.0 if t == 0 else t / ((dt * (dt - 1) - 2 * db) * 2)
        out[i] = (c, dt, None if weighted else t // 2)
    return out


def _size(out):
    return len(json.dumps(out, sort_keys=True).encode("utf-8"))


def run(store, graph_id=None, top_k=10, node=None, weighted=False, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. clustering_coefficient takes graph_id, top_k, "
                     f"node and weighted.")
    k, err = check_top_k(_as_top_k(top_k))
    if err:
        return err
    node = _as_node(g, node)
    if node is not None:
        err = check_node(g, node)
        if err:
            return err
    weighted = _as_bool(weighted, False)
    if not isinstance(weighted, bool):
        return error(f"weighted must be true or false; got {weighted!r}.")
    if g.number_of_nodes() == 0:
        return error(f"Graph '{graph_id}' has no nodes. Use list_graphs to pick another graph.")
    if weighted and any(not (w >= 0 and math.isfinite(w)) for _, _, w in g.edges()):
        return error(f"Graph '{graph_id}' has negative or non-finite edge weights, so weighted clustering is "
                     f"undefined. Call again with weighted=false.")

    stats = _directed(g, weighted) if g.directed else _undirected(g, weighted)
    n = g.number_of_nodes()
    average = sum(c for c, _, _ in stats.values()) / n
    kind = ("weighted " if weighted else "") + ("directed " if g.directed else "")
    avg_text = f"The average {kind}clustering of '{graph_id}' is {round(average, 6)} over {_plural(n, 'node')}."

    if node is not None:
        c, d, t = stats[node]
        result = node_ref(g, node, score=round(c, 6), degree=d, average_clustering=round(average, 6))
        if t is not None:
            result["triangles"] = t
        if d < 2:
            detail = "has fewer than two neighbours, so its clustering is 0"
        elif not g.directed and not weighted:
            detail = (f"has clustering {round(c, 6)}: {t} of the {_plural(d * (d - 1) // 2, 'pair')} of its "
                      f"{d} neighbours {'is' if t == 1 else 'are'} linked")
        else:
            detail = f"has {kind}clustering {round(c, 6)} ({d} {'in+out edges' if g.directed else 'neighbours'})"
        return ok(result, f"{g.label(node)} ({node}) {detail}. {avg_text}")

    # Rank on scores rounded to 12 places, so float noise from summation order cannot break a true tie;
    # ties are then broken by node id.
    key = {u: round(stats[u][0], 12) for u in stats}
    ranked = sorted(stats, key=lambda u: (-key[u], u))
    result = [node_ref(g, u, score=round(stats[u][0], 6)) for u in ranked[:k]]
    best = key[ranked[0]]
    if best == 0.0:
        summary = (f"No node in '{graph_id}' has linked neighbours (the graph has no triangles), so every "
                   f"clustering coefficient and the average are 0.")
    else:
        ties = sum(1 for u in ranked if key[u] == best)
        zeros = sum(1 for u in ranked if key[u] == 0.0)
        lead = f"{ties} nodes share the highest clustering" if ties > 1 else \
            f"{g.label(ranked[0])} ({ranked[0]}) has the highest clustering"
        summary = (f"{avg_text} {lead}, {round(best, 6)}; {zeros} node{' has' if zeros == 1 else 's have'} "
                   f"clustering 0.")
    out = ok(result, summary)
    while _size(out) > OUTPUT_BUDGET:  # long labels with top_k near 100: drop the lowest-ranked entries
        result.pop()
        out["summary"] = summary + f" Only the top {len(result)} nodes are listed to keep the response under 8 KB."
    return out
