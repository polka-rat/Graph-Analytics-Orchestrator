"""label_propagation tool.

Fast, deterministic community detection via asynchronous Label Propagation.
Registers community subgraphs with the store and returns result_graph_id.
"""
from __future__ import annotations

from collections import defaultdict
import random
from graphkit.contract import check_top_k, error, get_graph, node_ref, ok


def run(store, graph_id: str, max_iter: int = 30, seed: int = 0, top_k: int = 10, **params) -> dict:
    g, err = get_graph(store, graph_id)
    if err:
        return err

    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}.")

    k, err = check_top_k(top_k)
    if err:
        return err

    if not isinstance(max_iter, int) or max_iter < 1:
        return error(f"max_iter must be a positive integer; got {max_iter!r}.")

    nodes = g.nodes()
    if not nodes:
        return ok([], "Graph has no nodes.", result_graph_id=None)

    # Initialize each node with its own unique identifier
    community_assignments = {n: n for n in nodes}
    rng = random.Random(seed)

    # Asynchronous propagation loop
    for _ in range(max_iter):
        visitation_order = list(nodes)
        rng.shuffle(visitation_order)
        mutations = 0

        for u in visitation_order:
            nbr_weights = g.undirected_neighbors(u)
            if not nbr_weights:
                continue

            # Accumulate label affinity weighted by edge weight
            label_scores: dict[str, float] = defaultdict(float)
            for v, w in nbr_weights.items():
                label_scores[community_assignments[v]] += float(w)

            # Deterministic selection: highest weight first, lowest label string as tie-break
            winning_label = max(
                label_scores.keys(),
                key=lambda lbl: (label_scores[lbl], -len(lbl), lbl),
            )

            if community_assignments[u] != winning_label:
                community_assignments[u] = winning_label
                mutations += 1

        if mutations == 0:
            break

    # Group nodes into communities
    clusters: dict[str, list[str]] = defaultdict(list)
    for node, cid in community_assignments.items():
        clusters[cid].append(node)

    # Sort communities: largest size first, break ties by lowest member node ID
    sorted_clusters = sorted(clusters.values(), key=lambda mems: (-len(mems), sorted(mems)[0]))

    primary_subgraph_id = None
    output_communities = []

    for idx, member_nodes in enumerate(sorted_clusters[:k], 1):
        ordered_members = sorted(member_nodes)
        desc = f"LPA Community {idx} of '{graph_id}' ({len(ordered_members)} nodes)"
        sub_id = store.subgraph(graph_id, ordered_members, desc)

        if primary_subgraph_id is None:
            primary_subgraph_id = sub_id

        # Keep output compact to stay well under the 8 KB limit
        sample = [node_ref(g, n) for n in ordered_members[:8]]
        output_communities.append({
            "community_rank": idx,
            "size": len(ordered_members),
            "graph_id": sub_id,
            "sample_nodes": sample,
        })

    largest_size = len(sorted_clusters[0]) if sorted_clusters else 0
    summary = (
        f"Detected {len(sorted_clusters)} communities in '{graph_id}'. "
        f"The largest community contains {largest_size} nodes."
    )

    return ok(output_communities, summary, result_graph_id=primary_subgraph_id)