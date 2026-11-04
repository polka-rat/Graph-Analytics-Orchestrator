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


from collections import deque


def run(store, graph_id, source=None, sink=None, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error("Unknown parameters: " + ", ".join(sorted(params)))
    k, err = check_top_k(top_k)
    if err:
        return err
    for name, value in (("source", source), ("sink", sink)):
        err = check_node(g, value, name)
        if err:
            return err
    if source == sink:
        return error("source and sink must differ. Select two distinct node IDs.")
    nodes = sorted(g.nodes())
    residual = {u: {} for u in nodes}
    original = []
    for u, v, w in g.edges():
        if not math.isfinite(w) or w < 0:
            return error("Capacities must be finite and nonnegative. Select valid capacity weights.")
        if u == v:
            continue
        original.append((u, v, w))
        residual[u][v] = residual[u].get(v, 0.0) + w
        residual[v].setdefault(u, 0.0)
        if not g.directed:
            residual[v][u] += w
    order = {u: sorted(residual[u]) for u in nodes}
    value = 0.0
    while True:
        parent = {source: None}
        queue = deque([source])
        while queue and sink not in parent:
            u = queue.popleft()
            for v in order[u]:
                if v not in parent and residual[u][v] > 0:
                    parent[v] = u
                    queue.append(v)
                    if v == sink:
                        break
        if sink not in parent:
            reachable = set(parent)
            break
        amount = math.inf
        v = sink
        while v != source:
            u = parent[v]
            amount = min(amount, residual[u][v])
            v = u
        v = sink
        while v != source:
            u = parent[v]
            residual[u][v] -= amount
            residual[v][u] += amount
            v = u
        value += amount
        if not math.isfinite(value):
            return error("Flow exceeds the finite numeric range. Rescale capacities.")
    cut = []
    for u, v, w in original:
        if u in reachable and v not in reachable:
            cut.append((u, v, w))
        elif not g.directed and v in reachable and u not in reachable:
            cut.append((v, u, w))
    cut.sort(key=lambda e: (e[0], e[1]))
    capacity = math.fsum(w for _, _, w in cut)
    if not math.isfinite(capacity):
        return error("Cut capacity exceeds the numeric range. Rescale capacities.")
    result = {"source": node_ref(g, source), "sink": node_ref(g, sink),
              "max_flow": round(value, 6), "cut_capacity": round(capacity, 6),
              "cut_edges": [{"source": node_ref(g, u), "target": node_ref(g, v), "capacity": round(w, 6)}
                            for u, v, w in cut[:k]],
              "source_side": [node_ref(g, u) for u in sorted(reachable)[:k]],
              "sink_side": [node_ref(g, u) for u in nodes if u not in reachable][:k],
              "source_side_count": len(reachable), "sink_side_count": len(nodes) - len(reachable),
              "cut_edge_count": len(cut),
              "truncated": max(len(cut), len(reachable), len(nodes)-len(reachable)) > k}
    return bounded(result, f"Maximum flow is {value:.6f}, and minimum-cut capacity is {capacity:.6f}. Edge weights are treated as capacities; unweighted edges have capacity 1.")
