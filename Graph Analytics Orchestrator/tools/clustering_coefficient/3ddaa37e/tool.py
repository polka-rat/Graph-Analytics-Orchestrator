from graphkit.contract import check_node, check_top_k, error, get_graph, node_ref, ok
import json
import math


def bounded(result, summary, graph_id=None):
    output = ok(result, summary, graph_id)
    while len(json.dumps(output, ensure_ascii=True, allow_nan=False).encode()) > 8192:
        lists = [v for v in result.values() if isinstance(v, list) and v]
        if not lists:
            return error("Result exceeds 8 KB. Use nodes with shorter labels.")
        max(lists, key=lambda v: len(json.dumps(v))).pop()
        result["truncated"] = True
    return output


def run(store, graph_id, node=None, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error("Unknown parameters: " + ", ".join(sorted(params)))
    k, err = check_top_k(top_k)
    if err:
        return err
    if g.directed:
        return error("This tool supports undirected graphs. Select an undirected graph.")
    if node is not None:
        err = check_node(g, node)
        if err:
            return err
    nodes = sorted(g.nodes())
    if not nodes:
        return error("The graph is empty. Select a graph containing nodes.")
    scores = {}
    for u in nodes:
        neighbors = set(g.neighbors(u)) - {u}
        degree = len(neighbors)
        links = sum(len((set(g.neighbors(v)) - {v}) & neighbors) for v in neighbors) // 2
        scores[u] = 2 * links / (degree * (degree - 1)) if degree > 1 else 0.0
    average = math.fsum(scores.values()) / len(nodes)
    selected = [node] if node is not None else sorted(nodes, key=lambda u: (-scores[u], u))[:k]
    result = {"nodes": [node_ref(g, u, coefficient=round(scores[u], 6)) for u in selected],
              "average_clustering": round(average, 6), "node_count": len(nodes),
              "weighted": False, "truncated": len(selected) < len(nodes) if node is None else False}
    return bounded(result, f"Average clustering is {average:.6f} across {len(nodes)} nodes. Edge weights and self-loops are ignored.")
