"""Local clustering coefficient of a node, the graph's average clustering and its transitivity.

The local clustering of a node v with degree d >= 2 is 2*T(v) / (d*(d-1)), where T(v) is the
number of triangles through v. Nodes with degree < 2 have clustering 0. Directed graphs are
treated as undirected (edge direction is ignored); weights are ignored; self-loops are skipped.
"""
from graphkit.contract import check_node, check_top_k, error, get_graph, node_ref, ok


def _neighbour_sets(g):
    return {n: set(g.undirected_neighbors(n)) - {n} for n in g.nodes()}


def _local(nbrs, v):
    """(clustering, triangles, degree) of node v."""
    nv = nbrs[v]
    d = len(nv)
    if d < 2:
        return 0.0, 0, d
    links = sum(len(nbrs[u] & nv) for u in nv) // 2  # edges among v's neighbours
    return 2.0 * links / (d * (d - 1)), links, d


def run(store, graph_id, node=None, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     f"clustering_coefficient takes graph_id, node (optional) and top_k.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if node is not None:
        err = check_node(g, node)
        if err:
            return err
    n = g.number_of_nodes()
    if n == 0:
        return error(f"Graph '{graph_id}' has no nodes, so clustering is undefined. Pick another graph.")

    nbrs = _neighbour_sets(g)
    local = {v: _local(nbrs, v) for v in g.nodes()}
    avg = sum(c for c, _, _ in local.values()) / n
    triangles = sum(t for _, t, _ in local.values()) // 3
    triples = sum(d * (d - 1) // 2 for _, _, d in local.values())
    transitivity = 3.0 * triangles / triples if triples else 0.0
    note = " Edge direction was ignored." if g.directed else ""

    result = {"average_clustering": round(avg, 6), "transitivity": round(transitivity, 6),
              "triangles": triangles, "nodes": n}
    if node is not None:
        c, t, d = local[node]
        result["node"] = node_ref(g, node, clustering=round(c, 6), triangles=t, degree=d)
        if d < 2:
            why = f"it has only {d} neighbour{'s' if d != 1 else ''}, so no triangle is possible"
        else:
            why = f"{t} of the {d * (d - 1) // 2} possible links among its {d} neighbours exist"
        summary = (f"{g.label(node)} has local clustering {round(c, 6)} ({why}); "
                   f"the average clustering of '{graph_id}' is {round(avg, 6)}.{note}")
        return ok(result, summary)

    top = sorted(local.items(), key=lambda it: (-it[1][0], it[0]))[:k]
    result["top_nodes"] = [node_ref(g, v, clustering=round(c, 6), triangles=t, degree=d)
                           for v, (c, t, d) in top]
    summary = (f"'{graph_id}' has average clustering {round(avg, 6)} and transitivity "
               f"{round(transitivity, 6)} ({triangles} triangles among {n} nodes); "
               f"{g.label(top[0][0])} has the highest local clustering ({round(top[0][1][0], 6)}).{note}")
    return ok(result, summary)
