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


def run(store, graph_id, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error("Unknown parameters: " + ", ".join(sorted(params)))
    k, err = check_top_k(top_k)
    if err:
        return err
    if g.directed:
        return error("A spanning tree requires an undirected graph. Select an undirected graph.")
    nodes = sorted(g.nodes())
    if not nodes:
        return error("The graph is empty. Select a graph containing nodes.")
    edges = []
    for u, v, w in g.edges():
        if not math.isfinite(w):
            return error("All edge weights must be finite. Select a graph with finite weights.")
        if u != v:
            edges.append((w, min(u, v), max(u, v)))
    parent = {u: u for u in nodes}
    size = {u: 1 for u in nodes}

    def find(u):
        while parent[u] != u:
            parent[u] = parent[parent[u]]
            u = parent[u]
        return u

    chosen = []
    for w, u, v in sorted(edges):
        a, c = find(u), find(v)
        if a == c:
            continue
        if size[a] < size[c]:
            a, c = c, a
        parent[c] = a
        size[a] += size[c]
        chosen.append((u, v, w))
        if len(chosen) == len(nodes) - 1:
            break
    if len(chosen) != len(nodes) - 1:
        return error("The graph is disconnected, so no spanning tree exists. Select a connected subgraph.")
    try:
        total = math.fsum(w for _, _, w in chosen)
    except OverflowError:
        return error("Total weight exceeds the finite numeric range. Rescale the weights.")
    if not math.isfinite(total):
        return error("Total weight exceeds the finite numeric range. Rescale the weights.")
    child = (store.edge_subgraph(graph_id, [(u, v) for u, v, _ in chosen], "Minimum spanning tree")
             if chosen else store.subgraph(graph_id, nodes, "Single-node spanning tree"))
    result = {"edges": [{"source": node_ref(g, u), "target": node_ref(g, v), "weight": round(w, 6)}
                        for u, v, w in chosen[:k]], "total_weight": round(total, 6),
              "node_count": len(nodes), "edge_count": len(chosen), "truncated": len(chosen) > k}
    return bounded(result, f"The minimum spanning tree connects {len(nodes)} nodes with {len(chosen)} edges and total weight {total:.6f}. The registered graph contains the full tree.", child)
