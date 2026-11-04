"""node_embedding_similarity: cosine similarity of deterministic spectral node embeddings.

Rules (the validator checks them):
- Standard library, NumPy and graphkit only.
- Graphs come from the store only.
"""
import json
import math

import numpy as np

from graphkit.contract import (DEFAULT_TOP_K, MAX_OUTPUT_BYTES, check_node, check_top_k,
                               error, get_graph, node_ref, ok)

MAX_NODES = 1500
MAX_DIMENSIONS = 128
MAX_WALK_LENGTH = 10
EPS = 1e-9


def _check_int(value, name, low, high):
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        return error(f"{name} must be a whole number from {low} to {high}; got {value!r}.")
    return None


def _adjacency(g, ids, index, use_weights):
    """Dense symmetric adjacency matrix. Returns (A, None) or (None, error_dict)."""
    n = len(ids)
    A = np.zeros((n, n), dtype=float)
    for u in ids:
        i = index[u]
        for v, w in g.undirected_neighbors(u).items():
            if v == u:
                continue
            if use_weights:
                if not math.isfinite(w):
                    return None, error(f"Edge {u!r} - {v!r} has a non-finite weight ({w!r}). "
                                       "Use use_weights=false to ignore weights.")
                if w < 0:
                    return None, error(f"Edge {u!r} - {v!r} has a negative weight ({w!r}); "
                                       "random-walk embeddings need non-negative weights. "
                                       "Use use_weights=false to ignore weights.")
                if w == 0:
                    continue
                A[i, index[v]] = w
            else:
                A[i, index[v]] = 1.0
    return 0.5 * (A + A.T), None


def _embed(A, dimensions, walk_length):
    """Rows of Q_k * Lambda_k^t for the largest-|lambda| eigenpairs of D^-1/2 A D^-1/2.

    A group of tied |lambda| is never split, so cosine similarities do not depend on the
    arbitrary basis LAPACK picks inside an eigenspace. Returns (X, dimensions_used).
    """
    n = A.shape[0]
    deg = A.sum(axis=1)
    inv_sqrt = np.zeros(n)
    positive = deg > 0
    inv_sqrt[positive] = 1.0 / np.sqrt(deg[positive])
    S = A * inv_sqrt[:, None] * inv_sqrt[None, :]
    S = 0.5 * (S + S.T)

    vals, vecs = np.linalg.eigh(S)
    order = np.argsort(-np.abs(vals), kind="stable")
    vals, vecs = vals[order], vecs[:, order]
    mag = np.abs(vals)

    m = int(np.count_nonzero(mag > EPS))
    if m == 0:
        return np.zeros((n, 1)), 0
    k = min(dimensions, m)
    while k < m and mag[k - 1] - mag[k] < EPS:
        k += 1
    return vecs[:, :k] * np.power(vals[:k], walk_length), k


def _unit_rows(X):
    norms = np.linalg.norm(X, axis=1)
    good = norms > 1e-12
    out = np.zeros_like(X)
    out[good] = X[good] / norms[good, None]
    return out


def _round_scores(values):
    return np.round(np.clip(values, -1.0, 1.0), 6) + 0.0   # + 0.0 turns -0.0 into 0.0


def run(store, graph_id, node=None, top_k=DEFAULT_TOP_K, dimensions=16, walk_length=2,
        use_weights=False, seed=0, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. node_embedding_similarity takes "
                     "graph_id, node, top_k, dimensions, walk_length, use_weights and seed.")
    if node is not None:
        err = check_node(g, node)
        if err:
            return err
    top, err = check_top_k(top_k)
    if err:
        return err
    for value, name, low, high in ((dimensions, "dimensions", 1, MAX_DIMENSIONS),
                                   (walk_length, "walk_length", 1, MAX_WALK_LENGTH)):
        err = _check_int(value, name, low, high)
        if err:
            return err
    if not isinstance(use_weights, bool):
        return error(f"use_weights must be true or false; got {use_weights!r}.")
    if isinstance(seed, bool) or not isinstance(seed, int):
        return error(f"seed must be a whole number; got {seed!r}. (It has no effect: the method is deterministic.)")

    ids = sorted(g.nodes())          # index order == node id order, so index ties mean id ties
    n = len(ids)
    if n == 0:
        return error(f"Graph '{graph_id}' has no nodes. Use list_graphs to pick a graph with nodes.")
    if n > MAX_NODES:
        return error(f"Graph '{graph_id}' has {n} nodes; this tool handles at most {MAX_NODES}. "
                     "Use a smaller graph or a subgraph.")
    index = {u: i for i, u in enumerate(ids)}

    A, err = _adjacency(g, ids, index, use_weights)
    if err:
        return err
    try:
        X, used = _embed(A, dimensions, walk_length)
    except (np.linalg.LinAlgError, ValueError, FloatingPointError, MemoryError) as exc:
        return error(f"Could not compute the embedding: {type(exc).__name__}: {exc}")
    if not np.all(np.isfinite(X)):
        return error("The embedding contained non-finite values; try use_weights=false.")
    U = _unit_rows(X)

    notes = ""
    if used == 0:
        notes = " The graph has no usable edges, so every similarity is 0."
    how = (f"cosine similarity of {used}-dimensional spectral embeddings (walk length {walk_length})"
           if used else "cosine similarity of spectral embeddings")

    if node is not None:
        qi = index[node]
        scores = _round_scores(U @ U[qi])
        cand = np.delete(np.arange(n), qi)
        order = np.lexsort((cand, -scores[cand]))
        chosen = cand[order][:top]
        entries = [node_ref(g, ids[i], score=float(scores[i])) for i in chosen]
        total = n - 1
        name = f"{g.label(node)} ({node})"
        if np.linalg.norm(U[qi]) == 0.0 and used:
            notes += " The query node has no connections, so its similarity to every node is 0."
        head = f"nodes most similar to {name} in '{graph_id}'"
    else:
        total = n * (n - 1) // 2
        entries = []
        if total:
            sims = U @ U.T
            iu, ju = np.triu_indices(n, 1)
            neg = -_round_scores(sims[iu, ju])
            if total > top:
                cutoff = np.partition(neg, top - 1)[top - 1]
                keep = np.nonzero(neg <= cutoff)[0]
            else:
                keep = np.arange(total)
            order = np.lexsort((ju[keep], iu[keep], neg[keep]))
            for p in keep[order][:top]:
                entries.append({"node_a": node_ref(g, ids[iu[p]]), "node_b": node_ref(g, ids[ju[p]]),
                                "score": float(-neg[p])})
        head = f"most similar node pairs in '{graph_id}'"

    # Stay under the 8 KB output limit, leaving room for the summary.
    while entries and len(json.dumps(entries)) > MAX_OUTPUT_BYTES - 1024:
        entries.pop()

    if not entries:
        summary = f"No {head}: the graph has too few nodes.{notes}"
    elif node is not None:
        best = entries[0]
        summary = (f"{len(entries)} {head} are listed (of {total}), by {how}. "
                   f"The closest is {best['label']} ({best['id']}) with score {best['score']}.{notes}")
    else:
        best = entries[0]
        summary = (f"{len(entries)} {head} are listed (of {total} pairs), by {how}. "
                   f"The closest pair is {best['node_a']['label']} and {best['node_b']['label']} "
                   f"with score {best['score']}.{notes}")
    return ok(entries, summary)