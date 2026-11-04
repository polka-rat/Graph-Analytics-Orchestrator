"""Iterative Tarjan low-link search for undirected cut vertices and bridges."""
import json
from graphkit.contract import check_top_k, error, get_graph, node_ref, ok


def run(store, graph_id=None, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. Use graph_id and top_k.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if g.directed:
        return error("Articulation points and bridges require an undirected graph. Choose an undirected graph.")
    discovery, low, parent, children = {}, {}, {}, {}
    points, bridges = set(), []
    for root in sorted(g.nodes()):
        if root in discovery:
            continue
        discovery[root] = low[root] = len(discovery)
        parent[root], children[root] = None, 0
        stack = [(root, iter(g.neighbors(root)))]
        while stack:
            u, neighbors = stack[-1]
            v = next(neighbors, None)
            if v is not None:
                if v not in discovery:
                    parent[v], children[v] = u, 0
                    children[u] += 1
                    discovery[v] = low[v] = len(discovery)
                    stack.append((v, iter(g.neighbors(v))))
                elif v != parent[u]:
                    low[u] = min(low[u], discovery[v])
            else:
                stack.pop()
                p = parent[u]
                if p is None:
                    if children[u] > 1:
                        points.add(u)
                else:
                    low[p] = min(low[p], low[u])
                    if parent[p] is not None and low[u] >= discovery[p]:
                        points.add(p)
                    if low[u] > discovery[p]:
                        bridges.append(tuple(sorted((p, u))))
    result = {
        "articulation_points": [node_ref(g, n) for n in sorted(points)[:k]],
        "bridges": [{"source": node_ref(g, u), "target": node_ref(g, v)}
                    for u, v in sorted(bridges)[:k]],
        "articulation_point_count": len(points), "bridge_count": len(bridges),
        "truncated": len(points) > k or len(bridges) > k,
    }
    out = ok(result, f"Found {len(points)} articulation points and {len(bridges)} bridges; lists show at most {k} each.")
    # Long labels can exhaust the byte budget before reaching top_k.
    while len(json.dumps(out).encode()) > 8192:
        lists = [result['articulation_points'], result['bridges']]
        longest = max(lists, key=lambda x: len(json.dumps(x)))
        if not longest:
            return error("Result exceeds the response size limit; use shorter labels.")
        longest.pop()
        result['truncated'] = True
    return out
