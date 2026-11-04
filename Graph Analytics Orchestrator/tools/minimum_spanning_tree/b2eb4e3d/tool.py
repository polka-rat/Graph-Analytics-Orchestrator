"""minimum_spanning_tree: minimum spanning tree (or forest) of a graph, found with Kruskal's algorithm.

Rules (the validator checks them):
- Standard library, NumPy and graphkit only.
- Graphs come from the store only.
"""
import json
import math

from graphkit.contract import (DEFAULT_TOP_K, MAX_OUTPUT_BYTES, check_top_k, error,
                               get_graph, node_ref, ok)


def _find(parent, x):
    """Root of x's set, with path compression (iterative, so no recursion limit)."""
    root = x
    while parent[root] != root:
        root = parent[root]
    while parent[x] != root:
        parent[x], x = root, parent[x]
    return root


def _candidate_edges(g):
    """One candidate edge per unordered node pair: {(a, b): (weight, source, target)}.

    Self-loops are skipped. When a pair is joined in both directions, the smaller weight
    wins, ties going to the smaller (source, target). Returns (None, bad_edge) if any
    weight is not a finite number.
    """
    best = {}
    for u, v, w in g.edges():
        if u == v:
            continue
        if not math.isfinite(w):
            return None, (u, v, w)
        key = (u, v) if u <= v else (v, u)
        cand = (w, u, v) if g.directed else (w, key[0], key[1])
        if key not in best or cand < best[key]:
            best[key] = cand
    return best, None


def _register(store, graph_id, edges, description):
    """Register the tree once; an identical query reuses the same id (deterministic output)."""
    for meta in store.list_graphs():
        if meta["parent_id"] == graph_id and meta["description"] == description:
            return meta["graph_id"]
    return store.edge_subgraph(graph_id, edges, description)


def run(store, graph_id, top_k=DEFAULT_TOP_K, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. minimum_spanning_tree takes "
                     "graph_id and top_k.")
    top, err = check_top_k(top_k)
    if err:
        return err

    n = g.number_of_nodes()
    if n == 0:
        return error(f"Graph '{graph_id}' has no nodes, so it has no spanning tree. "
                     "Use list_graphs to pick a graph with nodes.")

    best, bad = _candidate_edges(g)
    if bad is not None:
        return error(f"Edge {bad[0]!r} -> {bad[1]!r} has a non-finite weight ({bad[2]!r}); "
                     "a spanning tree needs finite weights.")

    # Kruskal: take edges in order of (weight, id, id), skipping any that close a cycle.
    parent = {x: x for x in g.nodes()}
    size = {x: 1 for x in parent}
    tree = []
    for key in sorted(best, key=lambda k: (best[k][0], k[0], k[1])):
        if len(tree) == n - 1:
            break
        ra, rb = _find(parent, key[0]), _find(parent, key[1])
        if ra == rb:
            continue
        if size[ra] < size[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        size[ra] += size[rb]
        tree.append(best[key])

    total = round(math.fsum(w for w, _, _ in tree), 6)
    components = n - len(tree)
    connected = components == 1
    kind = "tree" if connected else "forest"

    sub_id = None
    if tree:
        description = f"Minimum spanning {kind} of {graph_id} (total weight {total})"
        try:
            sub_id = _register(store, graph_id, [(u, v) for _, u, v in tree], description)
        except (ValueError, KeyError) as exc:
            return error(f"Could not register the spanning {kind} as a subgraph: {exc}")

    result = {
        "total_weight": total,
        "num_nodes": n,
        "num_edges": len(tree),
        "num_components": components,
        "is_connected": connected,
        "weighted": g.weighted,
        "edges": [{"source": node_ref(g, u), "target": node_ref(g, v), "weight": round(w, 6)}
                  for w, u, v in tree[:top]],
        "truncated": False,
    }
    # Stay under the 8 KB output limit, leaving room for the summary.
    while result["edges"] and len(json.dumps(result)) > MAX_OUTPUT_BYTES - 1024:
        result["edges"].pop()
    result["truncated"] = len(result["edges"]) < len(tree)

    summary = (f"The minimum spanning {kind} of '{graph_id}' has {len(tree)} edges over {n} nodes "
               f"with total weight {total}")
    summary += "." if connected else f" ({components} components, so this is a forest)."
    if not g.weighted:
        summary += " The graph is unweighted, so every edge counts 1."
    if g.directed:
        summary += " Edge directions were ignored."
    if result["edges"]:
        summary += f" {len(result['edges'])} edges are listed, lightest first."
    if sub_id:
        summary += f" The tree is registered as graph '{sub_id}'."
    return ok(result, summary, result_graph_id=sub_id)