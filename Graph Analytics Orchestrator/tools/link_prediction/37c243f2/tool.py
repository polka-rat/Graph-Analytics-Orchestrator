"""Recommend missing links using common-neighbor similarity measures."""
import json
import math
from graphkit.contract import error, get_graph, node_ref, ok

VALID_METHODS = {"common_neighbors", "jaccard", "adamic_adar"}

def run(store, graph_id: str, method: str = "adamic_adar",
        top_k: int = 10, **params) -> dict:
    if params:
        return error(f"Unknown parameter(s): {', '.join(sorted(params))}.")

    g, err = get_graph(store, graph_id)
    if err:
        return err

    if not isinstance(method, str) or method not in VALID_METHODS:
        return error("Invalid method. Choose common_neighbors, jaccard, or adamic_adar.")

    if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1 or top_k > 100:
        return error("top_k must be a whole number from 1 to 100.")

    nodes = sorted(g.nodes())
    neighbors = {}
    for node in nodes:
        if g.directed:
            neighbors[node] = set(g.in_neighbors(node)) | set(g.out_neighbors(node))
        else:
            neighbors[node] = set(g.neighbors(node))

    candidates = []
    for i, u in enumerate(nodes):
        for v in nodes[i + 1:]:
            if v in neighbors[u] or u in neighbors[v]:
                continue

            common = neighbors[u] & neighbors[v]
            if not common:
                continue

            if method == "common_neighbors":
                score = float(len(common))
            elif method == "jaccard":
                union = neighbors[u] | neighbors[v]
                score = len(common) / len(union) if union else 0.0
            else:
                score = sum(
                    1.0 / math.log(len(neighbors[w]))
                    for w in common if len(neighbors[w]) > 1
                )

            if score > 0:
                candidates.append((u, v, score))

    candidates.sort(key=lambda item: (-item[2], item[0], item[1]))
    selected = candidates[:top_k]
    result = [
        {
            "source": node_ref(g, u),
            "target": node_ref(g, v),
            "score": round(score, 6),
            "method": method,
        }
        for u, v, score in selected
    ]

    # Keep the whole response under the 8 KB limit of the tool contract.
    while len(result) > 1 and len(json.dumps(result)) > 6500:
        result.pop()

    return ok(
        result,
        f"Found {len(candidates)} candidate missing link(s); returning {len(result)}."
    )
