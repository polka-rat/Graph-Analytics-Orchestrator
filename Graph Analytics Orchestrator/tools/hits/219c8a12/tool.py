import json

import numpy as np

from graphkit.contract import MAX_OUTPUT_BYTES, check_top_k, error, get_graph, node_ref, ok

TARGET_BYTES = min(7500, MAX_OUTPUT_BYTES)

SCORES = ("hub", "authority", "both")
MAX_ITER_LIMIT = 100_000


def _edge_arrays(g, nodes, use_weights):
    index = {n: i for i, n in enumerate(nodes)}
    src, dst, w = [], [], []
    for u, v, weight in g.edges():
        weight = weight if use_weights else 1.0
        src.append(index[u]); dst.append(index[v]); w.append(weight)
        if not g.directed and u != v:
            src.append(index[v]); dst.append(index[u]); w.append(weight)
    return np.array(src, dtype=np.int64), np.array(dst, dtype=np.int64), np.array(w, dtype=float)


def _power_iteration(src, dst, w, n, max_iter, tol):
    h = np.full(n, 1.0 / n)
    a = np.zeros(n)
    for it in range(1, max_iter + 1):
        h_last = h
        a = np.bincount(dst, weights=w * h[src], minlength=n)
        h = np.bincount(src, weights=w * a[dst], minlength=n)
        top = h.max()
        if top <= 0:
            return None, None, it, False
        h = h / top
        if np.abs(h - h_last).sum() < tol:
            return h, a, it, True
    return h, a, max_iter, False


def _size(out):
    return len(json.dumps(out, allow_nan=False, sort_keys=True).encode("utf-8"))


def run(store, graph_id, score="both", top_k=10, max_iter=100, tol=1e-8, normalized=True, weighted=True,
        **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. hits takes graph_id, score, top_k, max_iter, "
                     f"tol, normalized and weighted.")
    if score not in SCORES:
        return error(f"score must be 'hub', 'authority' or 'both'; got {score!r}.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if isinstance(max_iter, bool) or not isinstance(max_iter, int) or not 1 <= max_iter <= MAX_ITER_LIMIT:
        return error(f"max_iter must be a whole number from 1 to {MAX_ITER_LIMIT}; got {max_iter!r}.")
    if isinstance(tol, bool) or not isinstance(tol, (int, float)) or not 0 < tol < 1:
        return error(f"tol must be a positive number below 1 (default 1e-8); got {tol!r}.")
    if not isinstance(normalized, bool) or not isinstance(weighted, bool):
        return error("normalized and weighted must be true or false.")
    n = g.number_of_nodes()
    if n == 0 or g.number_of_edges() == 0:
        return error(f"HITS needs at least one edge, but graph '{graph_id}' has {g.number_of_edges()} edges. "
                     f"Use list_graphs to pick a graph with links.")

    nodes = g.nodes()
    use_weights = weighted and g.weighted
    src, dst, w = _edge_arrays(g, nodes, use_weights)
    if not np.all(np.isfinite(w)) or np.any(w < 0):
        return error(f"Graph '{graph_id}' has negative or non-finite edge weights; run hits with weighted=false.")
    h, a, iterations, converged = _power_iteration(src, dst, w, n, max_iter, tol)
    if h is None:
        return error(f"All edge weights in '{graph_id}' are zero, so HITS scores are undefined; "
                     f"run hits with weighted=false.")
    if normalized:
        h = h / h.sum()
        a = a / a.sum()
    else:
        a = a / a.max()

    hub = [round(float(x), 6) for x in h]
    auth = [round(float(x), 6) for x in a]

    def ranking(values):
        return sorted(range(n), key=lambda i: (-values[i], nodes[i]))

    lists = {}
    if score in ("hub", "both"):
        lists["hubs"] = ranking(hub)
    if score in ("authority", "both"):
        lists["authorities"] = ranking(auth)

    caveats = []
    if not converged:
        caveats.append(f"warning: did not converge within max_iter={max_iter} iterations (tol={tol}), so the scores "
                       f"are approximate; raise max_iter for a precise answer")
    caveats.append("scores sum to 1 within each ranking" if normalized else "scores are scaled so the largest is 1")
    if not g.directed:
        caveats.append("the graph is undirected, so hub and authority scores are identical")
    if use_weights:
        caveats.append("edge weights were used (set weighted=false to count every link equally)")
    elif g.weighted:
        caveats.append("edge weights were ignored (weighted=false)")

    shown = k
    while True:
        result = {}
        heads = []
        for key, order in lists.items():
            result[key] = [node_ref(g, nodes[i], hub=hub[i], authority=auth[i]) for i in order[:shown]]
            best = result[key][0]
            kind = "hub" if key == "hubs" else "authority"
            heads.append(f"the top {kind} is {best['label']} ({best['id']}, {kind} score {best[kind]})")
        result["iterations"] = iterations
        result["converged"] = converged
        lead = f"Among {n} nodes of '{graph_id}', " + " and ".join(heads) + "."
        extra = [f"only the top {shown} per ranking are listed to keep the response small"] if shown < min(k, n) else []
        second = "; ".join(caveats + extra) + "."
        out = ok(result, f"{lead} {second[0].upper()}{second[1:]}")
        if _size(out) <= TARGET_BYTES or shown == 1:
            return out
        shown = max(1, shown * 3 // 4)
