"""minimum_spanning_tree: cheapest set of edges that connects every node, found with Kruskal's algorithm.

Undirected graphs only. If the graph is not connected the result is a minimum spanning forest
(one tree per connected part), and the summary says so. Unweighted graphs count every edge as 1.
The chosen edges are registered with the store as a subgraph and returned in result_graph_id,
so other tools can run on the tree.
"""
import json

from graphkit.contract import MAX_OUTPUT_BYTES, check_top_k, error, get_graph, node_ref, ok

SIZE_BUDGET = MAX_OUTPUT_BYTES - 900  # room for summary and the other keys


class _UnionFind:
    def __init__(self, items):
        self.parent = {x: x for x in items}
        self.size = {x: 1 for x in items}

    def find(self, x):
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:  # path compression
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        return True


def _kruskal(g):
    """Return (chosen edges as (u, v, weight), number of connected components)."""
    nodes = g.nodes()
    uf = _UnionFind(nodes)
    # Sort by weight, then by node ids, so ties are always resolved the same way.
    edges = sorted(((w, min(u, v), max(u, v)) for u, v, w in g.edges()))
    chosen = []
    for w, u, v in edges:
        if uf.union(u, v):
            chosen.append((u, v, w))
            if len(chosen) == len(nodes) - 1:
                break
    components = len(nodes) - len(chosen)
    return chosen, components


def run(store, graph_id, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. minimum_spanning_tree takes graph_id and top_k.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if g.directed:
        return error(f"Graph '{graph_id}' is directed, but a minimum spanning tree needs an undirected graph. "
                     f"Use list_graphs to find an undirected graph (for example 'lesmis' or 'karate').")
    if g.number_of_nodes() == 0 or g.number_of_edges() == 0:
        return error(f"Graph '{graph_id}' has no edges, so it has no spanning tree. "
                     f"Choose a graph with at least one edge.")

    chosen, components = _kruskal(g)
    total = round(sum(w for _, _, w in chosen), 6)
    sub_id = store.edge_subgraph(
        graph_id, [(u, v) for u, v, _ in chosen],
        f"Minimum spanning {'tree' if components == 1 else 'forest'} of '{graph_id}' (total weight {total})")

    # Heaviest edges first are the most informative; ties by ids.
    shown = sorted(chosen, key=lambda e: (-e[2], e[0], e[1]))[:k]
    result = [{"source": node_ref(g, u), "target": node_ref(g, v), "weight": round(w, 6)} for u, v, w in shown]
    trimmed = False
    while len(result) > 1 and len(json.dumps(result)) > SIZE_BUDGET:  # keep the whole reply under 8 KB
        result.pop()
        trimmed = True

    kind = "tree" if components == 1 else f"forest of {components} trees (the graph has {components} connected parts)"
    weight_note = "" if g.weighted else " The graph is unweighted, so every edge counts as 1 and the total is the edge count."
    more = ""
    if len(chosen) > len(result):
        more = f" Showing the {len(result)} heaviest of {len(chosen)} edges" + (" (shortened to fit the size limit)" if trimmed else "") + "."
    summary = (f"The minimum spanning {kind} of '{graph_id}' has {len(chosen)} edges and total weight {total}."
               f"{weight_note}{more}")
    return ok(result, summary, result_graph_id=sub_id)
