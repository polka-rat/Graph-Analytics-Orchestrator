"""bipartite_check: can the nodes be split into two groups with no edge inside a group?

BFS 2-colouring of every connected component (edge direction is ignored). If the graph is
bipartite the two sides are registered as subgraphs; otherwise an odd cycle is returned as proof.
"""
from collections import deque

from graphkit.contract import DEFAULT_TOP_K, check_top_k, error, get_graph, node_ref, ok


def _chain_to_root(parent, node):
    chain = [node]
    while parent[chain[-1]] is not None:
        chain.append(parent[chain[-1]])
    return chain


def _odd_cycle(parent, u, v):
    """u and v are adjacent and got the same colour: join their BFS-tree paths into an odd cycle."""
    if u == v:
        return [u]  # self-loop
    up, vp = _chain_to_root(parent, u), _chain_to_root(parent, v)
    in_vp = set(vp)
    lca = next(n for n in up if n in in_vp)  # lowest common ancestor
    left = up[: up.index(lca) + 1]            # u ... lca
    right = vp[: vp.index(lca)]               # v ... (child of lca)
    return left + right[::-1]                 # u ... lca ... v   (edge v-u closes the cycle)


def run(store, graph_id, top_k=DEFAULT_TOP_K, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. bipartite_check takes graph_id and top_k.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if g.number_of_nodes() == 0:
        return error(f"Graph '{graph_id}' has no nodes, so there is nothing to check.")

    nbrs = {n: sorted(set(g.undirected_neighbors(n)) | set(g.out_neighbors(n))) for n in g.nodes()}
    color, parent = {}, {}
    n_components = 0
    for root in sorted(g.nodes()):
        if root in color:
            continue
        n_components += 1
        color[root], parent[root] = 0, None
        queue = deque([root])
        while queue:
            u = queue.popleft()
            for v in nbrs[u]:
                if v not in color:
                    color[v], parent[v] = 1 - color[u], u
                    queue.append(v)
                elif color[v] == color[u]:
                    cycle = _odd_cycle(parent, u, v)
                    sub_id = store.subgraph(graph_id, cycle, f"Odd cycle of '{graph_id}'")
                    shown = cycle[:50]
                    result = {"is_bipartite": False, "odd_cycle_length": len(cycle),
                              "odd_cycle": [node_ref(g, n) for n in shown], "graph_id": sub_id}
                    names = " -> ".join(g.label(n) for n in cycle[:6]) + (" -> ..." if len(cycle) > 6 else "")
                    return ok(result,
                              f"Graph '{graph_id}' is not bipartite: it contains an odd cycle of length "
                              f"{len(cycle)} ({names}), so the nodes cannot be split into two groups "
                              f"without an edge inside a group.",
                              result_graph_id=sub_id)

    sides = [sorted(n for n in g.nodes() if color[n] == c) for c in (0, 1)]
    entries = []
    for name, nodes in zip(("side_a", "side_b"), sides):
        sub_id = store.subgraph(graph_id, nodes, f"Bipartite {name.replace('_', ' ')} of '{graph_id}'")
        entries.append({"side": name, "size": len(nodes), "graph_id": sub_id,
                        "nodes": [node_ref(g, n) for n in nodes[:k]]})
    biggest = max(entries, key=lambda e: (e["size"], e["side"] == "side_a"))
    result = {"is_bipartite": True, "components": n_components, "sides": entries}
    summary = (f"Graph '{graph_id}' is bipartite: its {g.number_of_nodes()} nodes split into two groups of "
               f"{entries[0]['size']} and {entries[1]['size']} with no edge inside a group.")
    if n_components > 1:
        summary += f" It has {n_components} components, so the grouping is unique only within each component."
    return ok(result, summary, result_graph_id=biggest["graph_id"])
