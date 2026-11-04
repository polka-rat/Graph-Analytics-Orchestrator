"""Connected components of a graph, found by breadth-first search, with their sizes.

Undirected graphs give ordinary connected components. Directed graphs give weakly
connected components (edge direction ignored); use strongly_connected_components
for components where every node reaches every other along edge directions.
Each returned component is registered as a subgraph so other tools can run on it.
"""
from collections import deque

from graphkit.contract import check_top_k, error, get_graph, node_ref, ok

MAX_MEMBERS_SHOWN = 10  # members listed per component, to keep the output under 8 KB


def _components(g):
    """List of components (each a sorted list of node ids), largest first."""
    seen = set()
    comps = []
    for start in sorted(g.nodes()):
        if start in seen:
            continue
        seen.add(start)
        comp = [start]
        queue = deque([start])
        while queue:
            u = queue.popleft()
            for v in g.undirected_neighbors(u):
                if v not in seen:
                    seen.add(v)
                    comp.append(v)
                    queue.append(v)
        comps.append(sorted(comp))
    # Largest first; ties broken by the smallest node id in the component.
    comps.sort(key=lambda c: (-len(c), c[0]))
    return comps


def run(store, graph_id, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. connected_components takes graph_id and top_k.")
    k, err = check_top_k(top_k)
    if err:
        return err
    n = g.number_of_nodes()
    if n == 0:
        return error(f"Graph '{graph_id}' has no nodes, so it has no components. Use list_graphs to pick another graph.")

    comps = _components(g)
    kind = "weakly connected component" if g.directed else "connected component"

    result = []
    for rank, comp in enumerate(comps[:k], 1):
        sub_id = store.subgraph(graph_id, comp, f"{kind.capitalize()} #{rank} of '{graph_id}' ({len(comp)} nodes)")
        result.append({
            "rank": rank,
            "size": len(comp),
            "fraction_of_nodes": round(len(comp) / n, 6),
            "graph_id": sub_id,
            "members": [node_ref(g, m) for m in comp[:MAX_MEMBERS_SHOWN]],
            "members_truncated": len(comp) > MAX_MEMBERS_SHOWN,
        })

    largest = comps[0]
    isolated = sum(1 for c in comps if len(c) == 1)
    if len(comps) == 1:
        summary = f"'{graph_id}' is {'weakly ' if g.directed else ''}connected: all {n} nodes form a single component."
    else:
        summary = (f"'{graph_id}' has {len(comps)} {kind}s; the largest has {len(largest)} of {n} nodes "
                   f"({len(largest) / n:.1%}), and {isolated} node(s) are isolated.")
    if g.directed:
        summary += " Edge direction was ignored; use strongly_connected_components to respect it."
    return ok(result, summary, result_graph_id=result[0]["graph_id"])
