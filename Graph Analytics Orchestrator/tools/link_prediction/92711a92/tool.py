"""link_prediction: rank node pairs that are not yet linked by how likely an edge between them is.

Neighbourhood-based scores, the same definitions as NetworkX:
  adamic_adar             sum over common neighbours w of 1 / log(deg(w))
  resource_allocation     sum over common neighbours w of 1 / deg(w)
  jaccard                 |N(u) & N(v)| / |N(u) | N(v)|
  common_neighbors        |N(u) & N(v)|
  preferential_attachment deg(u) * deg(v)
Directed graphs are scored on their undirected version (a pair counts as linked if
an edge exists in either direction).
"""
import json
import math

from graphkit.contract import check_node, check_top_k, error, get_graph, node_ref, ok

METHODS = ("adamic_adar", "resource_allocation", "jaccard", "common_neighbors", "preferential_attachment")
BYTE_BUDGET = 7800  # stay under the 8 KB output limit


def _score(method, cn_weight_aa, cn_weight_ra, n_common, deg_u, deg_v):
    if method == "adamic_adar":
        return cn_weight_aa
    if method == "resource_allocation":
        return cn_weight_ra
    if method == "common_neighbors":
        return float(n_common)
    if method == "jaccard":
        union = deg_u + deg_v - n_common
        return n_common / union if union else 0.0
    return float(deg_u * deg_v)  # preferential_attachment


def run(store, graph_id, node=None, method="adamic_adar", top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     "link_prediction takes graph_id, node, method and top_k.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if method not in METHODS:
        return error(f"Unknown method {method!r}. Use one of: {', '.join(METHODS)}.")
    if node is not None:
        err = check_node(g, node)
        if err:
            return err

    nodes = sorted(g.nodes())
    nbrs = {n: set(g.undirected_neighbors(n)) - {n} for n in nodes}
    deg = {n: len(nbrs[n]) for n in nodes}

    # Accumulate common-neighbour statistics for every unlinked pair (u < v) that shares
    # at least one neighbour, by walking over each middle node w and pairs of its neighbours.
    stats = {}  # (u, v) -> [n_common, adamic_adar_sum, resource_allocation_sum]
    middles = nodes if node is None else sorted(nbrs[node])
    for w in middles:
        nw = sorted(nbrs[w])
        if len(nw) < 2:
            continue
        aa, ra = 1.0 / math.log(len(nw)), 1.0 / len(nw)
        if node is None:
            pairs = ((nw[i], nw[j]) for i in range(len(nw)) for j in range(i + 1, len(nw)))
        else:
            pairs = (((node, x) if node < x else (x, node)) for x in nw if x != node)
        for u, v in pairs:
            if v in nbrs[u]:
                continue  # already linked
            s = stats.get((u, v))
            if s is None:
                stats[(u, v)] = [1, aa, ra]
            else:
                s[0] += 1
                s[1] += aa
                s[2] += ra

    def make(u, v, s):
        n_common, aa, ra = s if s else (0, 0.0, 0.0)
        return (u, v, _score(method, aa, ra, n_common, deg[u], deg[v]), n_common)

    scored = [make(u, v, s) for (u, v), s in stats.items()]

    # Pairs with no common neighbour score 0 on every method except preferential attachment.
    # Include them when that method is used, or when too few positive pairs exist to fill top_k.
    if method == "preferential_attachment" or len(scored) < k:
        if node is None:
            cand = ((u, v) for i, u in enumerate(nodes) for v in nodes[i + 1:])
        else:
            cand = (((node, x) if node < x else (x, node)) for x in nodes if x != node)
        for u, v in cand:
            if (u, v) not in stats and v not in nbrs[u]:
                scored.append(make(u, v, None))

    if not scored:
        where = f"around '{node}'" if node else f"in '{graph_id}'"
        return error(f"No unlinked node pairs {where}: every possible edge already exists, so there is nothing to predict.")

    scored.sort(key=lambda t: (-t[2], t[0], t[1]))  # ties broken by node ids, ascending
    top = scored[:k]
    result = [{"source": node_ref(g, u), "target": node_ref(g, v), "score": round(s, 6), "common_neighbors": c}
              for u, v, s, c in top]

    best = result[0]
    note = " (edge direction ignored)" if g.directed else ""
    focus = f" for {g.label(node)}" if node else ""
    summary = (f"The most likely missing link{focus} by {method.replace('_', ' ')}{note} is "
               f"{best['source']['label']} - {best['target']['label']} (score {best['score']}, "
               f"{best['common_neighbors']} common neighbours), out of {len(scored)} unlinked pairs scored.")
    out = ok(result, summary)
    while len(result) > 1 and len(json.dumps(out)) > BYTE_BUDGET:  # trim to the size limit
        result.pop()
        out["summary"] = summary + f" Showing the top {len(result)} to stay within the 8 KB limit."
    return out
