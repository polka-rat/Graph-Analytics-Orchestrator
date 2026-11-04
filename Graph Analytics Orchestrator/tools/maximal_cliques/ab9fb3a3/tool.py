"""Largest maximal cliques using pivoted Bron-Kerbosch"""
from bisect import insort
import json

from graphkit.contract import MAX_OUTPUT_BYTES, check_top_k, error, get_graph, node_ref, ok


def _cliques(adjacency):
    # R: clique, P: candidates, X: explored nodes
    def frame(r, p, x):
        pivot = min(p | x, key=lambda u: (-len(p & adjacency[u]), u)) if p or x else None
        candidates = sorted(p - adjacency[pivot]) if pivot is not None else []
        return [r, p, x, iter(candidates)]

    stack = [frame((), set(adjacency), set())]
    while stack:
        r, p, x, branches = stack[-1]
        if not p and not x:
            if r:
                yield tuple(sorted(r))
            stack.pop()
            continue
        v = next(branches, None)
        if v is None:
            stack.pop()
            continue
        child = frame(r + (v,), p & adjacency[v], x & adjacency[v])
        p.remove(v)
        x.add(v)
        stack.append(child)


def run(store, graph_id, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(sorted(params))}. See tool.json.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if g.directed:
        return error("Maximal cliques require an undirected graph. Choose karate or lesmis.")
    if not g.number_of_nodes():
        return error("The graph is empty. Choose an undirected graph with at least one node.")
    adjacency = {u: set(g.neighbors(u)) - {u} for u in g.nodes()}
    best, total = [], 0
    for clique in _cliques(adjacency):
        total += 1
        key = (-len(clique), clique)
        if len(best) < k or key < best[-1]:
            insort(best, key)
            if len(best) > k:
                best.pop()
    result = [{"size": -size, "nodes": [node_ref(g, n) for n in clique], "graph_id": None}
              for size, clique in best]
    summary = (f"Found {total} maximal cliques; returning the largest {len(result)} "
               f"(maximum size {-best[0][0]}). Edge weights and self-loops are ignored.")
    # Check size before registering subgraphs
    preview = ok(result, summary, "reserved")
    if len(json.dumps(preview, sort_keys=True).encode("utf-8")) + (len(result) + 1) * (len(graph_id) + 64) > MAX_OUTPUT_BYTES:
        return error("Cliques exceed the 8 KB output limit. Reduce top_k or analyse a smaller subgraph.")
    for entry, (_, clique) in zip(result, best):
        entry["graph_id"] = store.subgraph(graph_id, clique, f"Maximal clique of {len(clique)} nodes")
    out = ok(result, summary, result_graph_id=result[0]["graph_id"])
    if len(json.dumps(out, sort_keys=True).encode("utf-8")) > MAX_OUTPUT_BYTES:
        return error("Cliques exceed 8 KB. Reduce top_k or analyse a smaller subgraph.")
    return out
