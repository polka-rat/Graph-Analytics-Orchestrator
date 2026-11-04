"""link_prediction: top-k likely missing edges.

Scores every pair of nodes that is NOT already connected and returns the
highest-scoring pairs. Five classic neighbourhood scores are available; their
definitions match NetworkX (N(x) is the neighbour set of x, d(x) = |N(x)|):

  adamic_adar             sum over common neighbours w of 1 / log d(w)   (default)
  resource_allocation     sum over common neighbours w of 1 / d(w)
  jaccard                 |N(u) & N(v)| / |N(u) | N(v)|
  common_neighbors        |N(u) & N(v)|
  preferential_attachment d(u) * d(v)

Directed graphs are scored on their undirected view (a pair counts as
connected if an edge exists in either direction). Pairs with score 0 are left
out. Ties are broken by node id: pairs are written (u, v) with u < v and
sorted by u, then v; in single-node mode by the candidate's id.

Algorithm (global mode): nodes are visited in ascending id order and each
node u is paired only with later nodes v. For the common-neighbour based
scores, the candidates v of u are exactly the nodes two hops away, found by
walking u -> w -> v, so the cost is O(sum of d(w)^2) rather than O(n^2).
Preferential attachment needs every non-adjacent pair and is computed one
row at a time with NumPy. Because pairs are produced in ascending (u, v)
order, a new pair can only enter the current top-k list by scoring strictly
higher than the k-th best, which keeps memory at O(k).
"""
import json
import math

import numpy as np

from graphkit.contract import error, node_ref, ok

DEFAULT_TOP_K = 10
MAX_TOP_K = 100
MAX_BYTES = 7500
METHODS = ("adamic_adar", "resource_allocation", "jaccard",
           "common_neighbors", "preferential_attachment")
METHOD_TEXT = {
    "adamic_adar": "Adamic-Adar index",
    "resource_allocation": "resource allocation index",
    "jaccard": "Jaccard coefficient",
    "common_neighbors": "number of common neighbours",
    "preferential_attachment": "preferential attachment score",
}


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def _sort_key(node):
    return (isinstance(node, str), node)


def _resolve(node, node_set):
    if node in node_set:
        return node
    text = str(node).strip()
    if text in node_set:
        return text
    try:
        number = int(text)
    except ValueError:
        return None
    return number if number in node_set else None


def _parse_top_k(top_k):
    if isinstance(top_k, bool):
        raise ValueError
    top_k = int(top_k)
    if top_k < 1:
        raise ValueError
    return min(top_k, MAX_TOP_K)


def _fit(items, build):
    response = build(items)
    while items and len(json.dumps(response, default=str)) > MAX_BYTES:
        items = items[:-1]
        response = build(items)
    return response


def _neighbour_sets(g, nodes):
    """Undirected neighbour sets without self-loops."""
    return {n: set(g.undirected_neighbors(n)) - {n} for n in nodes}


def _two_hop_scores(u, nbrs, method, keep):
    """Scores of u against every node two hops away that `keep` accepts.

    Returns {v: (score, common_neighbour_count)} for v not adjacent to u.
    """
    n_u = nbrs[u]
    acc = {}       # v -> accumulated weight
    cnt = {}       # v -> number of common neighbours
    for w in n_u:
        d_w = len(nbrs[w])
        if d_w < 2:
            continue                          # w touches only u: it is nobody's common neighbour
        if method == "adamic_adar":
            weight = 1.0 / math.log(d_w)
        elif method == "resource_allocation":
            weight = 1.0 / d_w
        else:
            weight = 1.0
        for v in nbrs[w]:
            if v == u or v in n_u or not keep(v):
                continue
            acc[v] = acc.get(v, 0.0) + weight
            cnt[v] = cnt.get(v, 0) + 1
    out = {}
    d_u = len(n_u)
    for v, c in cnt.items():
        if method == "jaccard":
            score = c / (d_u + len(nbrs[v]) - c)
        elif method == "common_neighbors":
            score = c
        else:
            score = round(acc[v], 6)
        out[v] = (round(score, 6) if isinstance(score, float) else score, c)
    return out


def _common_count(u, v, nbrs):
    return len(nbrs[u] & nbrs[v])


# ----------------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------------
def run(store, graph_id: str, **params) -> dict:
    try:
        return _run(store, graph_id, **params)
    except Exception as exc:
        return error(f"link_prediction failed unexpectedly: {exc}")


def _run(store, graph_id, method="adamic_adar", node=None, top_k=DEFAULT_TOP_K, **_ignored):
    try:
        g = store.get(graph_id)
    except Exception:
        return error(f"Graph '{graph_id}' not found. Use list_graphs to see the available graph ids.")

    method = str(method).lower().strip().replace("-", "_").replace(" ", "_")
    if method not in METHODS:
        return error(f"Unknown method '{method}'. Choose one of {list(METHODS)}.")
    try:
        top_k = _parse_top_k(top_k)
    except (TypeError, ValueError):
        return error(f"top_k must be a positive integer (at most {MAX_TOP_K}); got {top_k!r}.")

    nodes = sorted(g.nodes(), key=_sort_key)
    if len(nodes) < 2:
        return error(f"Graph '{graph_id}' has fewer than two nodes, so there are no pairs to predict.")
    node_set = set(nodes)
    nbrs = _neighbour_sets(g, nodes)
    view = " (on the undirected view of this directed graph)" if g.directed else ""

    if node is not None and str(node).strip() != "":
        target = _resolve(node, node_set)
        if target is None:
            return error(f"Node '{node}' not found in graph '{graph_id}'. Use lookup_node to find node ids.")
        return _single_node(g, target, nodes, nbrs, method, top_k, view)
    return _global(g, nodes, nbrs, method, top_k, view)


def _single_node(g, u, nodes, nbrs, method, top_k, view):
    """Best new neighbours for one node: 'Who should u connect with next?'"""
    if method == "preferential_attachment":
        d_u = len(nbrs[u])
        cands = [(len(nbrs[v]) * d_u, v, _common_count(u, v, nbrs))
                 for v in nodes if v != u and v not in nbrs[u]]
        cands = [c for c in cands if c[0] > 0]
    else:
        scores = _two_hop_scores(u, nbrs, method, keep=lambda v: True)
        cands = [(s, v, c) for v, (s, c) in scores.items() if s > 0]
    cands.sort(key=lambda t: (-t[0], _sort_key(t[1])))
    top = cands[:top_k]
    lu = g.label(u)

    def build(shown):
        result = [{"source": node_ref(g, u), "target": node_ref(g, v),
                   "score": s, "common_neighbors": c} for s, v, c in shown]
        if not shown:
            summary = (f"No new link can be predicted for {lu} with the {METHOD_TEXT[method]}{view}: "
                       f"it has no non-adjacent node with a positive score.")
        else:
            s, v, c = shown[0]
            summary = (f"By the {METHOD_TEXT[method]}{view}, {lu} is most likely to link to "
                       f"{g.label(v)} next (score {s}, {c} common neighbours). "
                       f"Showing {len(shown)} of {len(cands)} candidates.")
        return ok(result=result, summary=summary)

    return _fit(top, build)


def _global(g, nodes, nbrs, method, top_k, view):
    """Top-k non-adjacent pairs over the whole graph."""
    index = {n: i for i, n in enumerate(nodes)}
    best = []          # list of (score, i, j), kept sorted and at most top_k long
    total = 0          # number of pairs with a positive score

    def threshold():
        return best[-1][0] if len(best) == top_k else 0

    if method == "preferential_attachment":
        deg = np.array([len(nbrs[n]) for n in nodes], dtype=np.int64)
        for i, u in enumerate(nodes):
            if deg[i] == 0 or i == len(nodes) - 1:
                continue
            row = deg[i] * deg[i + 1:]
            for v in nbrs[u]:                       # remove existing edges
                j = index[v]
                if j > i:
                    row[j - i - 1] = 0
            total += int(np.count_nonzero(row))
            hits = np.nonzero(row > threshold())[0]
            if hits.size == 0:
                continue
            if hits.size > top_k:                    # keep best top_k of this row
                order = np.lexsort((hits, -row[hits]))[:top_k]
                hits = hits[order]
            best.extend((int(row[h]), i, i + 1 + int(h)) for h in hits)
            best.sort(key=lambda t: (-t[0], t[1], t[2]))
            del best[top_k:]
    else:
        for i, u in enumerate(nodes):
            scores = _two_hop_scores(u, nbrs, method, keep=lambda v, i=i: index[v] > i)
            total += sum(1 for s, _ in scores.values() if s > 0)
            thr = threshold()
            new = [(s, i, index[v]) for v, (s, _) in scores.items() if s > thr]
            if new:
                best.extend(new)
                best.sort(key=lambda t: (-t[0], t[1], t[2]))
                del best[top_k:]

    def build(shown):
        result = []
        for s, i, j in shown:
            u, v = nodes[i], nodes[j]
            result.append({"source": node_ref(g, u), "target": node_ref(g, v),
                           "score": s, "common_neighbors": _common_count(u, v, nbrs)})
        if not shown:
            summary = (f"No missing link has a positive {METHOD_TEXT[method]}{view}; "
                       f"no two unconnected nodes share a neighbour.")
        else:
            s, i, j = shown[0]
            summary = (f"By the {METHOD_TEXT[method]}{view}, the most likely missing link is "
                       f"{g.label(nodes[i])} - {g.label(nodes[j])} (score {s}). "
                       f"Showing {len(shown)} of {total} unconnected pairs with a positive score.")
        return ok(result=result, summary=summary)

    return _fit(best, build)
