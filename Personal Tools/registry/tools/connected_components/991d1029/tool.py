"""Connected components of an undirected graph, with their sizes (iterative DFS)."""
from graphkit.contract import check_top_k, error, get_graph, node_ref, ok

SAMPLE_SIZE = 10


def _components(g):
    seen, comps = set(), []
    for start in g.nodes():
        if start in seen:
            continue
        seen.add(start)
        comp, stack = [], [start]
        while stack:
            u = stack.pop()
            comp.append(u)
            for v in g.undirected_neighbors(u):
                if v not in seen:
                    seen.add(v)
                    stack.append(v)
        comps.append(comp)
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
    if g.directed:
        return error(f"Graph '{graph_id}' is directed; connected_components needs an undirected graph. "
                     f"Use strongly_connected_components for directed graphs, or pick an undirected graph "
                     f"such as karate or lesmis.")

    if g.number_of_nodes() == 0:
        return ok([], f"Graph '{graph_id}' has no nodes, so no components.")

    comps = [sorted(c) for c in _components(g)]
    comps.sort(key=lambda c: (-len(c), c[0]))

    result, first_id = [], None
    for i, comp in enumerate(comps[:k], 1):
        sub_id = store.subgraph(graph_id, comp, f"connected component {i} of '{graph_id}' ({len(comp)} nodes)")
        first_id = first_id or sub_id
        result.append({"component": i, "size": len(comp), "graph_id": sub_id,
                       "nodes": [node_ref(g, n) for n in comp[:SAMPLE_SIZE]]})

    n = len(comps)
    largest = len(comps[0])
    summary = (f"'{graph_id}' has {n} connected component{'s' if n != 1 else ''}; "
               f"the largest has {largest} of {g.number_of_nodes()} nodes.")
    if n > k:
        summary += f" Showing the {k} largest."
    return ok(result, summary, result_graph_id=first_id)
