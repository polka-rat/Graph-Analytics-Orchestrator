"""Common neighbours and Jaccard similarity"""
import json

from graphkit.contract import (MAX_OUTPUT_BYTES, check_node, check_top_k, error,
                               get_graph, node_ref, ok)


def run(store, graph_id, node_a=None, node_b=None, direction="all", top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(sorted(params))}. See tool.json.")
    for name, node in (("node_a", node_a), ("node_b", node_b)):
        err = check_node(g, node, name)
        if err:
            return err
    k, err = check_top_k(top_k)
    if err:
        return err
    if direction not in ("all", "in", "out"):
        return error("direction must be 'all', 'in', or 'out'.")
    neighbors = {"all": g.undirected_neighbors, "in": g.in_neighbors,
                 "out": g.out_neighbors}[direction]
    a = set(neighbors(node_a)) - {node_a}
    b = set(neighbors(node_b)) - {node_b}
    common, union = a & b, a | b
    score = round(len(common) / len(union), 6) if union else 0.0
    shown = sorted(common)[:k]
    result = {"node_a": node_ref(g, node_a), "node_b": node_ref(g, node_b),
              "direction": direction, "common_neighbor_count": len(common),
              "union_neighbor_count": len(union), "jaccard_score": score,
              "common_neighbors": [node_ref(g, n) for n in shown],
              "truncated": len(shown) < len(common)}
    out = ok(result, f"{g.label(node_a)} and {g.label(node_b)} have {len(common)} common "
             f"neighbours and Jaccard similarity {score} ({direction} neighbours; weights ignored).")
    if len(json.dumps(out, sort_keys=True).encode("utf-8")) > MAX_OUTPUT_BYTES:
        return error("Result exceeds 8 KB. Reduce top_k or use a subgraph with shorter labels.")
    return out
