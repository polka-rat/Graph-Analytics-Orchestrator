"""Finds the nodes that play the most similar role to a given node, using DeepWalk-style embeddings.

Algorithm (DeepWalk, Perozzi et al. 2014):
1. Random walks: from every node, walks_per_node uniform random walks of walk_length steps,
   moving to a random neighbour each step (edge direction ignored).
2. Skip-gram with negative sampling, written in NumPy: every node gets a vector of size
   `dimensions`. For each pair of nodes that appear within `window` steps of each other on a walk,
   the vectors are pulled together; for NEGATIVE random nodes (drawn from the walk frequency ** 0.75)
   they are pushed apart. Trained for `epochs` passes of mini-batch SGD with a decaying learning rate.
3. Similarity: cosine similarity between the query node's vector and every other node's vector.

Time roughly O(V * walks_per_node * walk_length * window * dimensions) per epoch.
Deterministic: all randomness comes from numpy.random.default_rng(seed).
"""
import json

import numpy as np

from graphkit.contract import MAX_OUTPUT_BYTES, check_node, check_top_k, error, get_graph, node_ref, ok
NEGATIVE = 5          # negative samples per positive pair
BATCH = 256          # positive pairs per SGD step
LR_START, LR_END = 0.025, 0.0001
MAX_WORK = 110_000_000  # pairs x epochs x dimensions; keeps every call well under the 30 s limit

LIMITS = {            # name: (default, minimum, maximum)
    "dimensions": (32, 2, 128),
    "walk_length": (20, 2, 80),
    "walks_per_node": (10, 1, 40),
    "window": (5, 1, 10),
    "epochs": (2, 1, 10),
}


def _check_int(name, value, lo, hi):
    if isinstance(value, bool) or not isinstance(value, int) or not lo <= value <= hi:
        return error(f"{name} must be a whole number from {lo} to {hi}; got {value!r}.")
    return None


def _random_walks(nbrs, n_nodes, walks_per_node, walk_length, rng):
    """Uniform random walks as a list of arrays of node indices."""
    walks = []
    for _ in range(walks_per_node):
        for start in rng.permutation(n_nodes):
            if not nbrs[start]:
                continue  # an isolated node has no walk
            walk = [start]
            for _ in range(walk_length - 1):
                options = nbrs[walk[-1]]
                walk.append(options[rng.integers(len(options))])
            walks.append(np.array(walk, dtype=np.int64))
    return walks


def _skipgram_pairs(walks, window):
    """All (centre, context) index pairs within `window` steps on the same walk."""
    centres, contexts = [], []
    for walk in walks:
        for offset in range(1, window + 1):
            if offset >= len(walk):
                break
            centres += [walk[:-offset], walk[offset:]]
            contexts += [walk[offset:], walk[:-offset]]
    return np.concatenate(centres), np.concatenate(contexts)


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -10, 10)))


def _scatter_add(matrix, rows, values):
    """matrix[rows] += values, adding up repeated rows (a fast replacement for np.add.at)."""
    n, d = matrix.shape
    flat = (rows[:, None] * d + np.arange(d)).ravel()
    matrix += np.bincount(flat, weights=values.ravel(), minlength=n * d).reshape(n, d)


def _train(n_nodes, centres, contexts, dimensions, epochs, rng):
    """Skip-gram with negative sampling. Returns the input (node) vectors."""
    w_in = (rng.random((n_nodes, dimensions)) - 0.5) / dimensions
    w_out = np.zeros((n_nodes, dimensions))
    freq = np.bincount(centres, minlength=n_nodes).astype(float) ** 0.75
    noise_cdf = np.cumsum(freq / freq.sum())
    noise_cdf[-1] = 1.0
    n_pairs = len(centres)
    total_steps = epochs * ((n_pairs + BATCH - 1) // BATCH)
    step = 0
    for _ in range(epochs):
        order = rng.permutation(n_pairs)
        for b in range(0, n_pairs, BATCH):
            lr = LR_START - (LR_START - LR_END) * step / total_steps
            step += 1
            idx = order[b:b + BATCH]
            c, o = centres[idx], contexts[idx]
            # Negative samples drawn from the noise distribution (inverse-CDF sampling).
            neg = np.searchsorted(noise_cdf, rng.random((len(idx), NEGATIVE)), side="right")
            v = w_in[c]                                          # (B, d)
            targets = np.concatenate([o[:, None], neg], axis=1)  # (B, 1 + NEGATIVE)
            u = w_out[targets]                                   # (B, 1 + NEGATIVE, d)
            labels = np.zeros(targets.shape)
            labels[:, 0] = 1.0
            # Gradient of the log-loss: (label - sigmoid(score)).
            g = (labels - _sigmoid(np.einsum("bd,bkd->bk", v, u))) * lr
            grad_in = np.einsum("bk,bkd->bd", g, u)
            grad_out = g[:, :, None] * v[:, None, :]
            _scatter_add(w_in, c, grad_in)
            _scatter_add(w_out, targets.ravel(), grad_out.reshape(-1, dimensions))
    return w_in

def run(store, graph_id, node=None, top_k=10, target=None, seed=0, dimensions=32, walk_length=20,
        walks_per_node=10, window=5, epochs=2, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. node_embedding_similarity takes graph_id, "
                     f"node, top_k, target, seed, dimensions, walk_length, walks_per_node, window and epochs.")
    if node is None:
        return error("Give the node to compare others with in 'node' (use lookup_node to find its id).")
    err = check_node(g, node)
    if err:
        return err
    if target is not None:
        err = check_node(g, target, param="target")
        if err:
            return err
    k, err = check_top_k(top_k)
    if err:
        return err
    if isinstance(seed, bool) or not isinstance(seed, int):
        return error(f"seed must be a whole number; got {seed!r}.")
    settings = {"dimensions": dimensions, "walk_length": walk_length, "walks_per_node": walks_per_node,
                "window": window, "epochs": epochs}
    for name, value in settings.items():
        _, lo, hi = LIMITS[name]
        err = _check_int(name, value, lo, hi)
        if err:
            return err

    ids = sorted(g.nodes())
    index = {n: i for i, n in enumerate(ids)}
    nbrs = [[index[v] for v in sorted(g.undirected_neighbors(n)) if v != n] for n in ids]
    if not nbrs[index[node]]:
        return error(f"{g.label(node)} ({node}) has no neighbours, so random walks never visit it and no "
                     f"embedding can be learned for it. Pick a node with at least one edge.")
    if target is not None and not nbrs[index[target]]:
        return error(f"{g.label(target)} ({target}) has no neighbours, so it has no embedding to compare with.")

    rng = np.random.default_rng(seed)
    walks = _random_walks(nbrs, len(ids), walks_per_node, walk_length, rng)
    centres, contexts = _skipgram_pairs(walks, window)
    work = len(centres) * epochs * dimensions
    if work > MAX_WORK:
        return error(f"These settings need about {work / MAX_WORK:.1f} times the allowed training work and "
                     f"would be too slow. Lower walks_per_node, walk_length, window, epochs or dimensions "
                     f"(the defaults work well).")
    vectors = _train(len(ids), centres, contexts, dimensions, epochs, rng)

    norms = np.linalg.norm(vectors, axis=1)
    norms[norms == 0] = 1.0
    unit = vectors / norms[:, None]
    q = index[node]
    sims = unit @ unit[q]
    direct = set(nbrs[q])

    # Rank every other node that has an embedding (isolated nodes have none).
    candidates = [i for i in range(len(ids)) if i != q and nbrs[i]]
    if not candidates:
        return error(f"{g.label(node)} ({node}) is the only node with edges in '{graph_id}', "
                     f"so there are no other nodes to compare it with.")
    ranked = sorted(candidates, key=lambda i: (-round(float(sims[i]), 6), ids[i]))
    similar = [node_ref(g, ids[i], score=round(float(sims[i]), 6), is_neighbor=i in direct)
               for i in ranked[:k]]

    result = {
        "node": node_ref(g, node),
        "similar": similar,
        "compared_with": len(candidates),
        "settings": {**settings, "seed": seed, "negative_samples": NEGATIVE,
                     "walks": len(walks), "edge_direction": "ignored" if g.directed else "undirected"},
    }
    if target is not None:
        t = index[target]
        rank = ranked.index(t) + 1
        result["target"] = node_ref(g, target, score=round(float(sims[t]), 6), rank=rank,
                                    is_neighbor=t in direct)
    # Keep the output under 8 KB (long labels on big graphs): list fewer nodes if needed.
    while len(similar) > 1 and len(json.dumps(result).encode("utf-8")) > MAX_OUTPUT_BYTES - 1000:
        similar.pop()
    best = similar[0]
    summary = (f"Using DeepWalk embeddings (seed {seed}), the node most similar to {g.label(node)} ({node}) is "
               f"{best['label']} ({best['id']}) with cosine similarity {best['score']}; "
               f"{len(similar)} of {len(candidates)} nodes are listed.")
    if target is not None:
        summary += (f" {g.label(target)} ({target}) has similarity {result['target']['score']} "
                    f"and ranks {rank} of {len(candidates)}.")
    return ok(result, summary)