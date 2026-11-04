"""Checks whether a graph is bipartite and returns its two sides, or an odd cycle that proves it is not.

Algorithm: breadth-first 2-colouring. Each connected component is started from its smallest node id
(side A); every neighbour gets the opposite side. The graph is bipartite exactly when no edge joins two
nodes of the same side. If such an edge (u, v) is found, the BFS-tree paths from u and v up to their
lowest common ancestor plus the edge (u, v) form an odd cycle, which is returned as proof.
Edge direction is ignored (as in networkx.is_bipartite). Time O(V + E).
"""
from collections import deque

from graphkit.contract import check_top_k, error, get_graph, node_ref, ok


def _adjacency(g):
    """Neighbours ignoring direction, sorted so the result is deterministic."""
    return {n: sorted(g.undirected_neighbors(n)) for n in g.nodes()}


def _two_colour(adj):
    """Returns (side, conflict, parent, depth, components).

    side: {node: 0 or 1}; conflict: None, or an edge (u, v) whose ends got the same side.
    """
    side, parent, depth = {}, {}, {}
    components = 0
    for start in sorted(adj):
        if start in side:
            continue
        components += 1
        side[start], parent[start], depth[start] = 0, None, 0
        queue = deque([start])
        while queue:
            u = queue.popleft()
            for v in adj[u]:
                if v not in side:
                    side[v], parent[v], depth[v] = 1 - side[u], u, depth[u] + 1
                    queue.append(v)
                elif side[v] == side[u]:
                    return side, (u, v), parent, depth, components
    return side, None, parent, depth, components


def _odd_cycle(u, v, parent, depth):
    """The cycle u -> ... -> LCA -> ... -> v -> u, as a list of nodes (odd length)."""
    if u == v:  # self-loop: a cycle of length 1
        return [u]
    path_u, path_v = [u], [v]
    a, b = u, v
    while depth[a] > depth[b]:
        a = parent[a]
        path_u.append(a)
    while depth[b] > depth[a]:
        b = parent[b]
        path_v.append(b)
    while a != b:
        a, b = parent[a], parent[b]
        path_u.append(a)
        path_v.append(b)
    # path_u ends at the LCA; path_v ends at the LCA too, so drop it once.
    return path_u + path_v[-2::-1]


def _edge(g, a, b):
    """The edge between a and b in the direction it exists in the graph."""
    return (a, b) if g.has_edge(a, b) else (b, a)


def run(store, graph_id, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. bipartite_check takes graph_id and top_k.")
    k, err = check_top_k(top_k)
    if err:
        return err
    n = g.number_of_nodes()
    if n == 0:
        return error(f"Graph '{graph_id}' has no nodes, so there is nothing to split. "
                     f"Use list_graphs to pick a non-empty graph.")

    adj = _adjacency(g)
    side, conflict, parent, depth, components = _two_colour(adj)
    direction_note = " Edge directions were ignored." if g.directed else ""

    if conflict is not None:
        cycle = _odd_cycle(conflict[0], conflict[1], parent, depth)
        cycle_edges = [_edge(g, cycle[i], cycle[(i + 1) % len(cycle)]) for i in range(len(cycle))]
        cycle_id = store.edge_subgraph(graph_id, cycle_edges,
                                       f"Odd cycle of length {len(cycle)} showing '{graph_id}' is not bipartite")
        shown = cycle[:k]
        result = {
            "is_bipartite": False,
            "odd_cycle_length": len(cycle),
            "odd_cycle": [node_ref(g, x) for x in shown],
            "odd_cycle_truncated": len(cycle) > k,
            "odd_cycle_graph_id": cycle_id,
        }
        names = " - ".join(g.label(x) for x in cycle[:6]) + (" - ..." if len(cycle) > 6 else "")
        summary = (f"'{graph_id}' is not bipartite: {names} form an odd cycle of length {len(cycle)}, "
                   f"so the nodes cannot be split into two groups with no links inside a group.{direction_note}")
        return ok(result, summary, result_graph_id=cycle_id)

    sides = {0: sorted(x for x in side if side[x] == 0), 1: sorted(x for x in side if side[x] == 1)}
    entries = []
    for s, name in ((0, "A"), (1, "B")):
        members = sides[s]
        sub_id = (store.subgraph(graph_id, members, f"Side {name} of the bipartite split of '{graph_id}'")
                  if members else None)
        entries.append({"side": name, "size": len(members), "graph_id": sub_id,
                        "sample": [node_ref(g, x) for x in members[:k]],
                        "sample_truncated": len(members) > k})
    largest = max(entries, key=lambda e: e["size"])  # ties: side A, as max keeps the first
    result = {"is_bipartite": True, "components": components, "edges": g.number_of_edges(), "sides": entries}
    a, b = entries
    comp_note = (f" The graph has {components} connected components; each is coloured starting from its "
                 f"smallest node id on side A, so other splits are equally valid." if components > 1 else "")
    summary = (f"'{graph_id}' is bipartite: its {n} nodes split into side A ({a['size']} nodes, e.g. "
               f"{', '.join(x['label'] for x in a['sample'][:3]) or 'none'}) and side B ({b['size']} nodes, e.g. "
               f"{', '.join(x['label'] for x in b['sample'][:3]) or 'none'}) with every edge between the two "
               f"sides.{comp_note}{direction_note}")
    return ok(result, summary, result_graph_id=largest["graph_id"])
