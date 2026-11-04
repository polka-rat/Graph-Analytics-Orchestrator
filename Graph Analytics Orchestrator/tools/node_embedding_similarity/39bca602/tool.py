"""node_embedding_similarity tool.

Computes structural role representations via random-walk Skip-Gram matrix
factorization (DeepWalk SVD) and retrieves nearest nodes by cosine similarity.
Implemented strictly with NumPy and standard library.
"""
from __future__ import annotations

import random
import numpy as np
from graphkit.contract import (
    check_node,
    check_top_k,
    error,
    get_graph,
    node_ref,
    ok,
)


def run(
    store,
    graph_id: str,
    node: str = None,
    dimensions: int = 16,
    walk_length: int = 10,
    num_walks: int = 5,
    window_size: int = 2,
    seed: int = 0,
    top_k: int = 10,
    **params,
) -> dict:
    g, err = get_graph(store, graph_id)
    if err:
        return err

    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}.")

    if node is None:
        return error("Parameter 'node' is required. Use lookup_node to find node IDs.")

    err = check_node(g, node, param="node")
    if err:
        return err

    k, err = check_top_k(top_k)
    if err:
        return err

    nodes = g.nodes()
    total_nodes = len(nodes)
    if total_nodes < 2:
        return ok([], "Graph has insufficient nodes to compute similarity.")

    node_to_idx = {nid: i for i, nid in enumerate(nodes)}
    idx_to_node = {i: nid for i, nid in enumerate(nodes)}
    target_idx = node_to_idx[node]

    # Pre-cache neighbor index arrays for efficient random walks
    adj_list = []
    for nid in nodes:
        nbrs = list(g.undirected_neighbors(nid).keys())
        adj_list.append(nbrs if nbrs else [nid])

    rng = random.Random(seed)

    # Build co-occurrence matrix via simulated random walks
    cooccur = np.zeros((total_nodes, total_nodes), dtype=np.float32)

    for _ in range(num_walks):
        node_order = list(range(total_nodes))
        rng.shuffle(node_order)

        for start_i in node_order:
            walk = [start_i]
            for _ in range(walk_length - 1):
                cur_nbrs = adj_list[walk[-1]]
                next_step = rng.choice(cur_nbrs)
                walk.append(node_to_idx[next_step])

            # Sliding context window accumulation
            w_size = len(walk)
            for pos, focal_node in enumerate(walk):
                lower = max(0, pos - window_size)
                upper = min(w_size, pos + window_size + 1)
                for ctx_pos in range(lower, upper):
                    if pos != ctx_pos:
                        context_node = walk[ctx_pos]
                        cooccur[focal_node, context_node] += 1.0

    # Derive Shifted Positive Pointwise Mutual Information (PPMI)
    grand_sum = float(cooccur.sum())
    if grand_sum == 0.0:
        grand_sum = 1.0

    p_joint = cooccur / grand_sum
    p_row = p_joint.sum(axis=1, keepdims=True)
    p_col = p_joint.sum(axis=0, keepdims=True)

    independent_prob = p_row @ p_col
    valid_mask = (p_joint > 0) & (independent_prob > 0)

    ppmi = np.zeros_like(p_joint)
    ppmi[valid_mask] = np.maximum(0.0, np.log(p_joint[valid_mask] / independent_prob[valid_mask]))

    # Truncated SVD factorization for dense vector representation
    latent_dim = min(dimensions, total_nodes)
    try:
        u_vectors, s_values, _ = np.linalg.svd(ppmi, full_matrices=False)
        embeddings = u_vectors[:, :latent_dim] * np.sqrt(s_values[:latent_dim])
    except Exception:
        embeddings = ppmi[:, :latent_dim]

    # L2-normalization for cosine distance evaluation
    magnitudes = np.linalg.norm(embeddings, axis=1, keepdims=True)
    magnitudes[magnitudes == 0.0] = 1.0
    normalized_vecs = embeddings / magnitudes

    target_vector = normalized_vecs[target_idx]
    cosine_scores = normalized_vecs @ target_vector

    scored_nodes = []
    for idx, raw_score in enumerate(cosine_scores):
        if idx == target_idx:
            continue
        scored_nodes.append((idx_to_node[idx], float(raw_score)))

    # Tie-breaking: score descending, node id ascending
    scored_nodes.sort(key=lambda pair: (-pair[1], str(pair[0])))
    top_ranked = scored_nodes[:k]

    result = [
        node_ref(g, nid, score=round(s, 6))
        for nid, s in top_ranked
    ]

    best_match = result[0] if result else None
    if best_match:
        summary = (
            f"The most structurally equivalent node to {g.label(node)} is {best_match['label']} "
            f"with an embedding cosine similarity of {best_match['score']}."
        )
    else:
        summary = f"No structurally similar nodes found for {g.label(node)}."

    return ok(result, summary)