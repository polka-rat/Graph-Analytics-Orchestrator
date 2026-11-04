"""personalized_pagerank: PageRank whose random surfer teleports back to chosen seed node(s).

Power iteration on the (weighted) transition matrix, written with NumPy.
Each iteration is O(E); about log(1e-12) / log(damping) iterations are needed.
"""
import json

import numpy as np

from graphkit.contract import check_node, check_top_k, error, get_graph, node_ref, ok

MAX_ITER = 2000
MAX_OUTPUT_BYTES = 7800  # the contract allows 8 KB; stay safely below it
TOLERANCE = 1e-12


def _seed_list(node, seeds):
    """Return (list_of_seed_ids, error_message_or_None); duplicates removed, order kept."""
    ids = []
    if node is not None:
        ids.append(node)
    if seeds is not None:
        if not isinstance(seeds, (list, tuple)):
         return None, "seeds must be a list of node IDs."

        if any(not isinstance(s, str) or not s for s in seeds):
         return None, "Every seed must be a non-empty node ID string."

        ids.extend(seeds)
    if not ids:
        return None, ("Give the seed node in 'node' (or several in 'seeds'). "
                      "Use lookup_node to find node ids from names.")
    return list(dict.fromkeys(ids)), None


def run(store, graph_id, node=None, seeds=None, damping=0.85, top_k=10, use_weights=True,
        exclude_seeds=False, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. personalized_pagerank takes graph_id, node, "
                     f"seeds, damping, top_k, use_weights and exclude_seeds.")
    seed_ids, msg = _seed_list(node, seeds)
    if msg:
        return error(msg)
    for s in seed_ids:
        err = check_node(g, s, "node" if s == node else "seeds")
        if err:
            return err
    if isinstance(damping, bool) or not isinstance(damping, (int, float)) or not 0 <= damping < 1:
        return error(f"damping must be a number from 0 up to (not including) 1; got {damping!r}. "
                     f"The usual value is 0.85.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if not isinstance(use_weights, bool) or not isinstance(exclude_seeds, bool):
        return error("use_weights and exclude_seeds must be true or false.")

    nodes = g.nodes()
    n = len(nodes)
    index = {v: i for i, v in enumerate(nodes)}
    weighted = use_weights and g.weighted
    src, dst, wts = [], [], []
    for u in nodes:
        for v, w in g.out_neighbors(u).items():  # on undirected graphs this lists every neighbour
            w = float(w) if weighted else 1.0
            if w < 0:
                return error(f"Graph '{graph_id}' has a negative edge weight; set use_weights=false.")
            if w > 0:
                src.append(index[u]); dst.append(index[v]); wts.append(w)
    src = np.array(src, dtype=np.int64)
    dst = np.array(dst, dtype=np.int64)
    wts = np.array(wts, dtype=float)
    out_strength = np.bincount(src, weights=wts, minlength=n)
    dangling = out_strength == 0
    share = wts / out_strength[src] if len(src) else wts  # probability of taking each edge

    p = np.zeros(n)
    for s in seed_ids:
        p[index[s]] = 1.0 / len(seed_ids)

    x = p.copy()
    converged = False

    for _ in range(MAX_ITER):
        walk = (
            np.bincount(dst, weights=x[src] * share, minlength=n)
            if len(src)
            else np.zeros(n)
        )

        new = (
            damping * (walk + x[dangling].sum() * p)
            + (1 - damping) * p
        )

        if np.abs(new - x).sum() < TOLERANCE:
            x = new
            converged = True
            break
        x = new

    if not converged:
        return error(
            f"Personalized PageRank did not converge within {MAX_ITER} "
            "iterations. Try a smaller damping value."
    )

    x = x / x.sum()

    seed_set = set(seed_ids)
    scored = [(nodes[i], round(float(x[i]), 6)) for i in range(n) if not (exclude_seeds and nodes[i] in seed_set)]
    if not scored:
        return error("Every node is a seed, so nothing is left to rank. Use exclude_seeds=false.")
    scored.sort(key=lambda item: (-item[1], item[0]))
    top = scored[:k]
    result = [node_ref(g, v, score=sc, rank=r) for r, (v, sc) in enumerate(top, 1)]

    seed_names = ", ".join(f"{g.label(s)} ({s})" for s in seed_ids[:3]) + (", ..." if len(seed_ids) > 3 else "")
    best = result[0]
    summary = (f"Personalized PageRank from {seed_names} (damping {damping}): {best['label']} ({best['id']}) "
               f"ranks first of {len(scored)} nodes with score {best['score']}"
               + (", excluding the seeds." if exclude_seeds else
                  "; the seed itself usually scores highest, so set exclude_seeds=true to see only other nodes."
                  if best["id"] in seed_set else "."))
    out = ok(result, summary)
    full = len(result)
    while len(result) > 1 and len(json.dumps(out)) > MAX_OUTPUT_BYTES:  # long labels: trim the tail
        result.pop()
    if len(result) < full:
        out["summary"] += f" (List shortened to the top {len(result)} to fit the 8 KB output limit.)"
    return out
