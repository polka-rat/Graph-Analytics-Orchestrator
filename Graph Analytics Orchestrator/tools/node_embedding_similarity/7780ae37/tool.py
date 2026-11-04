"""node_embedding_similarity: DeepWalk-style node embeddings and the nodes most similar to a query node.

Pipeline: seeded random walks -> skip-gram style co-occurrence counts inside a window ->
positive pointwise mutual information (PPMI) -> truncated SVD -> cosine similarity.
(Levy & Goldberg showed that skip-gram with negative sampling implicitly factorises a shifted PMI
matrix, so PPMI + SVD is a deterministic stand-in for training word2vec on the walks.)
"""
import math
import random

import numpy as np

from graphkit.contract import DEFAULT_TOP_K, check_node, check_top_k, error, get_graph, node_ref, ok

MAX_NODES = 3000  # the PPMI matrix is dense (n x n)
BOUNDS = {"dimensions": (1, 128), "walk_length": (2, 100), "num_walks": (1, 100), "window": (1, 10)}


def _int_param(name, value):
    lo, hi = BOUNDS[name]
    if isinstance(value, bool) or not isinstance(value, int) or not lo <= value <= hi:
        return error(f"{name} must be a whole number from {lo} to {hi}; got {value!r}.")
    return None


def _walks(nodes, nbrs, num_walks, walk_length, seed):
    """num_walks uniform random walks of walk_length nodes from every non-isolated node."""
    rng = random.Random(seed)
    index = {n: i for i, n in enumerate(nodes)}
    adj = [[index[v] for v in nbrs[n]] for n in nodes]
    starts = [i for i in range(len(nodes)) if adj[i]]
    walks = []
    for _ in range(num_walks):
        rng.shuffle(starts)
        for s in starts:
            walk, cur = [s], s
            for _ in range(walk_length - 1):
                cur = adj[cur][rng.randrange(len(adj[cur]))]
                walk.append(cur)
            walks.append(walk)
    return np.array(walks, dtype=np.int64)


def _embeddings(n, walks, window, dimensions):
    """Rows are unit-length node vectors; all-zero rows for nodes that never appear in a walk."""
    counts = np.zeros(n * n, dtype=np.float64)
    for off in range(1, min(window, walks.shape[1] - 1) + 1):
        a, b = walks[:, :-off].ravel(), walks[:, off:].ravel()
        counts += np.bincount(a * n + b, minlength=n * n)
        counts += np.bincount(b * n + a, minlength=n * n)
    C = counts.reshape(n, n)
    total = C.sum()
    row = C.sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        pmi = np.log(C * total / np.outer(row, row))
    ppmi = np.where(np.isfinite(pmi) & (pmi > 0), pmi, 0.0)
    U, S, _ = np.linalg.svd(ppmi, full_matrices=False)
    d = max(1, min(dimensions, n - 1))
    emb = U[:, :d] * np.sqrt(S[:d])
    norms = np.linalg.norm(emb, axis=1, keepdims=True)
    return np.divide(emb, norms, out=np.zeros_like(emb), where=norms > 1e-12)


def run(store, graph_id, node=None, top_k=DEFAULT_TOP_K, seed=0, dimensions=32, walk_length=40,
        num_walks=40, window=5, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. See the tool description for its parameters.")
    err = check_node(g, node)
    if err:
        return err
    k, err = check_top_k(top_k)
    if err:
        return err
    if isinstance(seed, bool) or not isinstance(seed, int):
        return error(f"seed must be a whole number; got {seed!r}.")
    for name, value in (("dimensions", dimensions), ("walk_length", walk_length),
                        ("num_walks", num_walks), ("window", window)):
        err = _int_param(name, value)
        if err:
            return err
    n = g.number_of_nodes()
    if n < 2:
        return error(f"Graph '{graph_id}' has only {n} node; embeddings need at least 2 nodes.")
    if n > MAX_NODES:
        return error(f"Graph '{graph_id}' has {n} nodes; this tool supports at most {MAX_NODES}. "
                     f"Use a smaller subgraph (for example from ego_network or k_hop_neighborhood).")

    nodes = sorted(g.nodes())
    pos = {v: i for i, v in enumerate(nodes)}
    nbrs = {v: sorted(g.undirected_neighbors(v)) for v in nodes}  # direction is ignored
    q = pos[node]
    qref = node_ref(g, node)
    if not nbrs[node]:
        return ok([], f"{qref['label']} has no connections in '{graph_id}', so random walks cannot reach "
                      f"anything and no similar nodes can be computed.")

    walks = _walks(nodes, nbrs, num_walks, walk_length, seed)
    emb = _embeddings(n, walks, window, dimensions)
    sims = emb @ emb[q]
    scored = [(round(float(sims[i]), 6), nodes[i]) for i in range(n) if i != q and nbrs[nodes[i]]]
    scored.sort(key=lambda item: (-item[0], item[1]))
    top = scored[:k]
    result = [node_ref(g, v, score=s) for s, v in top]
    if not result:
        return ok([], f"No other connected nodes exist in '{graph_id}' to compare with {qref['label']}.")
    summary = (f"The node most similar to {qref['label']} in '{graph_id}' is {result[0]['label']} "
               f"(cosine similarity {result[0]['score']}); showing {len(result)} nearest of {len(scored)} "
               f"connected nodes using {dimensions}-dimension random-walk embeddings (seed {seed}).")
    return ok(result, summary)
