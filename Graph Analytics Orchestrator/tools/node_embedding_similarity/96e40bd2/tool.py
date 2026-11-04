"""node_embedding_similarity: DeepWalk-style node embeddings and the nodes most similar to a query node.

Method (all written here with NumPy only):
1. Random walks. From every node start `num_walks` walks of `walk_length` nodes, choosing the next node
   uniformly among the current node's out-neighbours (a walk stops at a node with no out-edges).
2. Skip-gram counts. Every pair of nodes at most `window` steps apart in a walk is a (node, context) pair.
3. Embedding. DeepWalk's skip-gram with negative sampling implicitly factorises the shifted PMI matrix of
   these co-occurrences (Levy and Goldberg, 2014), so we build the positive PMI matrix directly and take its
   truncated SVD: embedding = U[:, :d] * sqrt(S[:d]). This is deterministic for a given seed and fast.
4. Similarity. Cosine similarity between the query node's vector and every other node's vector.

Randomness comes only from numpy.random.default_rng(seed), seed defaults to 0.
"""
import json
import math

import numpy as np

from graphkit.contract import MAX_OUTPUT_BYTES, check_node, check_top_k, error, get_graph, node_ref, ok

MAX_NODES = 3000            # the PMI matrix is dense (n x n)
MAX_WALK_POSITIONS = 4_000_000  # n * num_walks * walk_length
SIZE_BUDGET = MAX_OUTPUT_BYTES - 900

INT_PARAMS = {  # name: (default, minimum, maximum)
    "walk_length": (20, 2, 100),
    "num_walks": (10, 1, 100),
    "window": (5, 1, 10),
    "dimensions": (32, 2, 128),
    "seed": (0, 0, 2**32 - 1),
}


def _check_int(name, value):
    default, lo, hi = INT_PARAMS[name]
    if isinstance(value, bool) or not isinstance(value, int) or not lo <= value <= hi:
        return error(f"{name} must be a whole number from {lo} to {hi}; got {value!r} (default {default}).")
    return None


def _walks(g, nodes, index, num_walks, walk_length, rng):
    """All random walks as an int array (n * num_walks, walk_length); -1 marks 'walk already ended'."""
    n = len(nodes)
    indptr = np.zeros(n + 1, dtype=np.int64)
    neighbours = []
    for i, node in enumerate(nodes):
        nbrs = sorted(index[v] for v in g.out_neighbors(node))
        neighbours.extend(nbrs)
        indptr[i + 1] = indptr[i] + len(nbrs)
    indices = np.array(neighbours, dtype=np.int64)
    degree = np.diff(indptr)

    walks = np.full((n * num_walks, walk_length), -1, dtype=np.int64)
    current = np.tile(np.arange(n, dtype=np.int64), num_walks)
    walks[:, 0] = current
    alive = np.ones(len(current), dtype=bool)
    for step in range(1, walk_length):
        alive &= degree[np.where(alive, current, 0)] > 0
        if not alive.any():
            break
        cur = current[alive]
        pick = np.minimum((rng.random(cur.size) * degree[cur]).astype(np.int64), degree[cur] - 1)
        current = current.copy()
        current[alive] = indices[indptr[cur] + pick]
        walks[alive, step] = current[alive]
    return walks


def _cooccurrence(walks, n, window):
    """Symmetric count matrix of (node, context) pairs within `window` steps along the walks."""
    counts = np.zeros(n * n, dtype=np.float64)
    length = walks.shape[1]
    for offset in range(1, min(window, length - 1) + 1):
        a, b = walks[:, :-offset].ravel(), walks[:, offset:].ravel()
        valid = (a >= 0) & (b >= 0)
        a, b = a[valid], b[valid]
        counts += np.bincount(a * n + b, minlength=n * n)
        counts += np.bincount(b * n + a, minlength=n * n)
    return counts.reshape(n, n)


def _embed(counts, dimensions):
    total = counts.sum()
    row = counts.sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        pmi = np.log(counts * total / np.outer(row, row))
    ppmi = np.where(counts > 0, np.maximum(pmi, 0.0), 0.0)
    u, s, _ = np.linalg.svd(ppmi, full_matrices=False)
    d = min(dimensions, len(s))
    return u[:, :d] * np.sqrt(s[:d])


def run(store, graph_id, node=None, top_k=10, walk_length=20, num_walks=10, window=5, dimensions=32, seed=0,
        **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. node_embedding_similarity takes graph_id, node, "
                     f"top_k, walk_length, num_walks, window, dimensions and seed.")
    err = check_node(g, node)
    if err:
        return err
    k, err = check_top_k(top_k)
    if err:
        return err
    given = {"walk_length": walk_length, "num_walks": num_walks, "window": window,
             "dimensions": dimensions, "seed": seed}
    for name, value in given.items():
        err = _check_int(name, value)
        if err:
            return err

    nodes = g.nodes()
    n = len(nodes)
    if n < 3:
        return error(f"Graph '{graph_id}' has only {n} nodes; embeddings need at least 3.")
    if n > MAX_NODES:
        return error(f"Graph '{graph_id}' has {n} nodes; this tool handles up to {MAX_NODES}. "
                     f"Use filter_nodes to build a smaller subgraph first.")
    if n * num_walks * walk_length > MAX_WALK_POSITIONS:
        return error("The requested walks are too many for the time limit. Lower num_walks or walk_length.")
    if not g.out_neighbors(node) and not g.in_neighbors(node):
        return error(f"Node '{node}' has no edges, so random walks cannot reach it and it has no embedding. "
                     f"Pick a node that has connections (node_degree shows how many).")

    index = {v: i for i, v in enumerate(nodes)}
    rng = np.random.default_rng(seed)
    walks = _walks(g, nodes, index, num_walks, walk_length, rng)
    counts = _cooccurrence(walks, n, window)
    q = index[node]
    if counts[q].sum() == 0:
        return error(f"Node '{node}' never co-occurs with another node in the random walks (it may be a dead end "
                     f"with no incoming edges). Try a node with both incoming and outgoing edges.")
    emb = _embed(counts, dimensions)
    norms = np.linalg.norm(emb, axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        sims = (emb @ emb[q]) / (norms * norms[q])
    sims = np.nan_to_num(sims, nan=0.0)

    scored = [(round(float(sims[i]), 6), nodes[i]) for i in range(n) if i != q]
    scored.sort(key=lambda item: (-item[0], item[1]))  # ties by node id, ascending
    result = [node_ref(g, v, score=s) for s, v in scored[:k]]
    while len(result) > 1 and len(json.dumps(result)) > SIZE_BUDGET:
        result.pop()

    top = result[0]
    summary = (f"The node most similar to {g.label(node)} ({node}) in '{graph_id}' is {top['label']} "
               f"(cosine similarity {top['score']}); {len(result)} nearest nodes returned, based on "
               f"{dimensions}-dimensional DeepWalk-style embeddings (seed {seed}).")
    return ok(result, summary)
