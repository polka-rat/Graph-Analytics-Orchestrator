"""Node similarity from DeepWalk-style random-walk embeddings.
"""
import random

import numpy as np

from graphkit.contract import check_node, check_top_k, error, get_graph, node_ref, ok

MAX_DIMENSIONS = 64
DEFAULT_DIMENSIONS = 16
MAX_WALK_LENGTH = 100
MAX_WALKS_PER_NODE = 100
MAX_WINDOW = 20


def _check_int(name, value, low, high):
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        return None, error(
            f"{name} must be a whole number from {low} to {high}; got {value!r}."
        )
    return value, None


def _random_walk_embeddings(
    g, dimensions, walk_length, walks_per_node, window, seed
):
    nodes = g.nodes()
    n = len(nodes)
    index = {node: i for i, node in enumerate(nodes)}
    cooccurrence = np.zeros((n, n), dtype=np.int64)
    rng = random.Random(seed)

    for start in nodes:
        for _ in range(walks_per_node):
            walk = [start]
            for _ in range(walk_length - 1):
                neighbours = list(g.undirected_neighbors(walk[-1]).keys())
                if not neighbours:
                    break
                walk.append(rng.choice(neighbours))

            for i, center in enumerate(walk):
                center_index = index[center]
                lo = max(0, i - window)
                hi = min(len(walk), i + window + 1)
                for j in range(lo, hi):
                    if j != i:
                        cooccurrence[center_index, index[walk[j]]] += 1

    total = int(cooccurrence.sum())
    if total == 0:
        return nodes, np.zeros((n, max(1, min(dimensions, n))), dtype=float)

    row = cooccurrence.sum(axis=1)
    col = cooccurrence.sum(axis=0)
    expected = np.outer(row, col)
    pmi = np.zeros_like(cooccurrence, dtype=float)
    mask = (cooccurrence > 0) & (expected > 0)
    pmi[mask] = np.log(cooccurrence[mask] * total / expected[mask])
    ppmi = np.maximum(pmi, 0.0)

    values, vectors = np.linalg.eigh(ppmi)
    order = np.argsort(np.abs(values))[::-1]
    d = max(1, min(dimensions, n))
    values = values[order[:d]]
    vectors = vectors[:, order[:d]]
    embedding = vectors * np.sqrt(np.abs(values))[None, :]

    # Eigenvectors are defined up to sign; fix a sign for reproducibility.
    for column in range(embedding.shape[1]):
        pivot = int(np.argmax(np.abs(embedding[:, column])))
        if embedding[pivot, column] < 0:
            embedding[:, column] *= -1.0

    norms = np.linalg.norm(embedding, axis=1)
    norms[norms == 0] = 1.0
    return nodes, embedding / norms[:, None]


def run(
    store,
    graph_id,
    node=None,
    top_k=10,
    dimensions=DEFAULT_DIMENSIONS,
    walk_length=20,
    walks_per_node=10,
    window=5,
    seed=0,
    **params,
):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(
            f"Unknown parameter(s): {', '.join(params)}. "
            "node_embedding_similarity takes graph_id, node, top_k, dimensions, "
            "walk_length, walks_per_node, window and seed."
        )

    err = check_node(g, node)
    if err:
        return err
    k, err = check_top_k(top_k)
    if err:
        return err
    for name, value, low, high in (
        ("dimensions", dimensions, 2, MAX_DIMENSIONS),
        ("walk_length", walk_length, 2, MAX_WALK_LENGTH),
        ("walks_per_node", walks_per_node, 1, MAX_WALKS_PER_NODE),
        ("window", window, 1, MAX_WINDOW),
    ):
        _, err = _check_int(name, value, low, high)
        if err:
            return err
    if isinstance(seed, bool) or not isinstance(seed, int):
        return error(f"seed must be a whole number; got {seed!r}.")
    if g.number_of_nodes() < 2:
        return error(
            f"Graph '{graph_id}' has fewer than two nodes, so there is nothing to compare."
        )
    if not g.undirected_neighbors(node):
        return error(
            f"Node '{node}' ({g.label(node)}) has no neighbours in '{graph_id}', so it "
            "has no random-walk context and no meaningful embedding. Choose a connected "
            "node, or use lookup_node to find one."
        )

    nodes, embedding = _random_walk_embeddings(
        g, dimensions, walk_length, walks_per_node, window, seed
    )
    query_index = nodes.index(node)
    similarities = np.clip(embedding @ embedding[query_index], -1.0, 1.0)

    ranked = []
    for i, other in enumerate(nodes):
        if i == query_index:
            continue
        ranked.append((round(float(similarities[i]), 6), other))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    top = ranked[:k]

    result = [node_ref(g, other, score=score) for score, other in top]
    if not result:
        return ok(
            [],
            f"Graph '{graph_id}' has no other node to compare with "
            f"{g.label(node)} ({node}).",
        )
    best = result[0]
    summary = (
        f"Most similar to {g.label(node)} ({node}) in '{graph_id}' using a "
        f"{min(int(dimensions), g.number_of_nodes())}-dimensional DeepWalk-style "
        f"random-walk embedding: {best['label']} ({best['id']}) with cosine "
        f"similarity {best['score']}."
    )
    return ok(result, summary)
