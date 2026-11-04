"""node_embedding_similarity: DeepWalk-style random-walk embeddings and nearest nodes.

1. Simulate `num_walks` uniform random walks of `walk_length` steps from every node.
2. Count how often two nodes appear within `window` steps of each other on a walk
   (the co-occurrence statistics that DeepWalk's skip-gram model learns from).
3. Turn the counts into a positive PMI matrix and factorise it with a truncated SVD
   (the closed-form equivalent of skip-gram with negative sampling), giving each node a
   `dimensions`-dimensional vector.
4. Rank all other nodes by cosine similarity to the query node.

Everything is seeded, so the same call always gives the same answer.
"""
import json

import numpy as np

from graphkit.contract import MAX_OUTPUT_BYTES, check_top_k, error, get_graph, node_ref, ok

MAX_NODES = 5000
SAFE_BYTES = MAX_OUTPUT_BYTES - 1024


def _int_param(value, name, low, high):
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        return error(f"{name} must be a whole number from {low} to {high}; got {value!r}.")
    return None


def _csr(g, nodes, idx):
    """Neighbour lists (edge direction ignored) as CSR arrays, neighbours in node order."""
    indptr = [0]
    indices = []
    for u in nodes:
        nbrs = sorted(idx[v] for v in g.undirected_neighbors(u) if v != u)
        indices.extend(nbrs)
        indptr.append(len(indices))
    return np.array(indptr, dtype=np.int64), np.array(indices, dtype=np.int64)


def _walks(indptr, indices, n, num_walks, walk_length, rng):
    """Matrix of shape (n * num_walks, walk_length): one random walk per row."""
    cur = np.tile(np.arange(n, dtype=np.int64), num_walks)
    out = np.empty((len(cur), walk_length), dtype=np.int64)
    out[:, 0] = cur
    for step in range(1, walk_length):
        start = indptr[cur]
        deg = indptr[cur + 1] - start
        pick = start + np.floor(rng.random(len(cur)) * np.maximum(deg, 1)).astype(np.int64)
        nxt = np.where(deg > 0, indices[np.minimum(pick, max(len(indices) - 1, 0))] if len(indices) else cur, cur)
        cur = nxt
        out[:, step] = cur
    return out


def _embed(g, nodes, dimensions, walk_length, num_walks, window, seed):
    n = len(nodes)
    idx = {v: i for i, v in enumerate(nodes)}
    indptr, indices = _csr(g, nodes, idx)
    rng = np.random.default_rng(seed)
    walks = _walks(indptr, indices, n, num_walks, walk_length, rng)

    counts = np.zeros(n * n, dtype=np.float64)
    for offset in range(1, min(window, walk_length - 1) + 1):
        a = walks[:, :-offset].ravel()
        b = walks[:, offset:].ravel()
        counts += np.bincount(a * n + b, minlength=n * n)
        counts += np.bincount(b * n + a, minlength=n * n)
    C = counts.reshape(n, n)

    total = C.sum()
    row = C.sum(axis=1)
    ppmi = np.zeros_like(C)
    nz = C > 0
    rr, cc = np.nonzero(nz)
    ppmi[rr, cc] = np.log(C[rr, cc] * total / (row[rr] * row[cc]))
    np.maximum(ppmi, 0.0, out=ppmi)

    U, S, _ = np.linalg.svd(ppmi, full_matrices=False)
    d = min(dimensions, n)
    return U[:, :d] * np.sqrt(S[:d])


def run(store, graph_id, node=None, top_k=10, dimensions=16, walk_length=40, num_walks=10,
        window=5, seed=0, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. node_embedding_similarity takes graph_id, "
                     f"node, top_k, dimensions, walk_length, num_walks, window and seed.")
    if node is None:
        return error("Give the node to find similar nodes for in 'node'. Use lookup_node to find a node id.")
    if not isinstance(node, str) or not g.has_node(node):
        return error(f"Node '{node}' (parameter 'node') is not in graph '{graph_id}'. "
                     f"Use lookup_node to find node ids.")
    k, err = check_top_k(top_k)
    if err:
        return err
    for value, name, low, high in ((dimensions, "dimensions", 1, 128), (walk_length, "walk_length", 2, 200),
                                   (num_walks, "num_walks", 1, 50), (window, "window", 1, 20),
                                   (seed, "seed", 0, 2**32 - 1)):
        err = _int_param(value, name, low, high)
        if err:
            return err

    nodes = g.nodes()
    n = len(nodes)
    if n < 3:
        return error(f"Graph '{graph_id}' has only {n} nodes; embeddings need at least 3.")
    if n > MAX_NODES:
        return error(f"Graph '{graph_id}' has {n} nodes; this tool handles at most {MAX_NODES}. "
                     f"Use filter_nodes to build a smaller subgraph first.")

    emb = _embed(g, nodes, dimensions, walk_length, num_walks, window, seed)
    norms = np.linalg.norm(emb, axis=1)
    unit = np.divide(emb, norms[:, None], out=np.zeros_like(emb), where=norms[:, None] > 1e-12)
    q = nodes.index(node)
    sims = np.round(unit @ unit[q], 6)

    ranked = sorted(((-float(sims[i]), nodes[i]) for i in range(n) if i != q))
    result = [node_ref(g, v, score=round(-s + 0.0, 6)) for s, v in ranked[:k]]
    trimmed = False
    while len(result) > 1 and len(json.dumps(result)) > SAFE_BYTES:
        result.pop()
        trimmed = True

    best = result[0]
    summary = (f"The node most similar to {g.label(node)} ({node}) is {best['label']} ({best['id']}) with cosine "
               f"similarity {best['score']}, from {emb.shape[1]}-dimensional random-walk embeddings "
               f"(seed {seed}). Returning {len(result)} nodes"
               f"{' (shortened to fit the output size limit)' if trimmed else ''}.")
    return ok(result, summary)
