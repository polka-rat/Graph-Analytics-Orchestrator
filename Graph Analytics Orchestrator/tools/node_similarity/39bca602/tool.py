"""node_similarity tool.

Calculates common neighbors and Jaccard similarity scores.
Uses two-hop neighbor traversal for sub-millisecond ranking on large networks.
"""
from __future__ import annotations

import json
from graphkit.contract import (
    MAX_OUTPUT_BYTES,
    check_node,
    check_top_k,
    error,
    get_graph,
    node_ref,
    ok,
)

PAYLOAD_BUDGET = MAX_OUTPUT_BYTES - 600  # Leave headroom for summary and envelopes
VALID_DIRECTIONS = {"undirected", "out", "in", "any"}


def _get_adj(graph, node: str, mode: str) -> set[str]:
    """Retrieve neighbor set based on directed traversal mode."""
    if not graph.directed or mode in ("undirected", "any"):
        return set(graph.undirected_neighbors(node))
    if mode == "out":
        return set(graph.out_neighbors(node))
    return set(graph.in_neighbors(node))


def _get_incomers(graph, node: str, mode: str) -> set[str]:
    """Retrieve nodes that point to this node under the selected mode."""
    if not graph.directed or mode in ("undirected", "any"):
        return set(graph.undirected_neighbors(node))
    if mode == "out":
        return set(graph.in_neighbors(node))
    return set(graph.out_neighbors(node))


def _constrain_size(items: list, renderer):
    """Dynamically truncates trailing items to strictly respect 8 KB."""
    envelope = renderer(items)
    while items and len(json.dumps(envelope, default=str).encode("utf-8")) > PAYLOAD_BUDGET:
        items = items[:-1]
        envelope = renderer(items)
    return envelope


def run(store, graph_id: str, **params) -> dict:
    g, err = get_graph(store, graph_id)
    if err:
        return err

    # Support canonical names as well as peer parameter aliases
    query_node = params.pop("node", None) or params.pop("node_a", None)
    target_node = params.pop("target_node", None) or params.pop("node_b", None)
    mode = str(params.pop("direction", "undirected")).lower()
    top_k = params.pop("top_k", 10)

    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}.")

    if not query_node:
        return error("Parameter 'node' is required. Use lookup_node to find node IDs.")

    err = check_node(g, query_node, param="node")
    if err:
        return err

    if mode not in VALID_DIRECTIONS:
        return error(f"direction must be one of {sorted(VALID_DIRECTIONS)}; got '{mode}'.")

    nbrs_query = _get_adj(g, query_node, mode)
    mode_text = f" ({mode})" if g.directed and mode != "undirected" else ""

    # ---------------- 1. Pairwise Comparison Mode ----------------
    if target_node is not None:
        err = check_node(g, target_node, param="target_node")
        if err:
            return err

        if query_node == target_node:
            return error("Target node cannot be the same as reference node; provide two distinct nodes.")

        nbrs_target = _get_adj(g, target_node, mode)
        common_nodes = sorted(nbrs_query & nbrs_target)
        union_size = len(nbrs_query | nbrs_target)
        jaccard_score = round(len(common_nodes) / union_size, 6) if union_size else 0.0

        def render_pair(subset):
            res = {
                "node": node_ref(g, query_node),
                "target_node": node_ref(g, target_node),
                "direction": mode,
                "common_neighbors_count": len(common_nodes),
                "jaccard_similarity": jaccard_score,
                "common_neighbors": [node_ref(g, x) for x in subset],
            }
            summary = (
                f"{g.label(query_node)} and {g.label(target_node)} share {len(common_nodes)} "
                f"common neighbor(s){mode_text} with a Jaccard similarity of {jaccard_score}."
            )
            return ok(res, summary)

        return _constrain_size(common_nodes[:100], render_pair)

    # ---------------- 2. Top-k Ranking Mode ----------------
    k, err = check_top_k(top_k)
    if err:
        return err

    # 2-hop inverted lookup: candidate nodes must share at least 1 neighbor
    overlap_counts: dict[str, int] = {}
    for bridge in nbrs_query:
        for candidate in _get_incomers(g, bridge, mode):
            if candidate != query_node:
                overlap_counts[candidate] = overlap_counts.get(candidate, 0) + 1

    ranked = []
    for candidate, overlap in overlap_counts.items():
        nbrs_cand = _get_adj(g, candidate, mode)
        total_union = len(nbrs_query) + len(nbrs_cand) - overlap
        sim = round(overlap / total_union, 6) if total_union else 0.0
        ranked.append((candidate, sim, overlap))

    # Tie-breaking: score descending, node id ascending
    ranked.sort(key=lambda item: (-item[1], str(item[0])))
    top_entries = ranked[:k]

    def render_ranking(shown):
        res = [
            node_ref(g, cid, score=s, common_neighbors=c)
            for cid, s, c in shown
        ]
        if not shown:
            summary = f"{g.label(query_node)} shares no neighbors{mode_text} with any other node."
        else:
            top_node = shown[0]
            summary = (
                f"The most similar node to {g.label(query_node)}{mode_text} is {g.label(top_node[0])} "
                f"with Jaccard similarity {top_node[1]} ({top_node[2]} mutual neighbors)."
            )
        return ok(res, summary)

    return _constrain_size(top_entries, render_ranking)