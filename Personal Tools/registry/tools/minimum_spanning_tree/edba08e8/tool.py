"""minimum_spanning_tree: Kruskal's algorithm with union-find on an undirected graph.

On a disconnected graph it returns a minimum spanning forest (one tree per component).
Registers the tree as a subgraph and returns its id in result_graph_id.
"""
import json

from graphkit.contract import check_top_k, error, get_graph, node_ref, ok

MAX_RESULT_BYTES = 6500  # the whole response must stay under 8 KB


class _UnionFind:
    def __init__(self, items):
        self.parent = {x: x for x in items}
        self.rank = {x: 0 for x in items}

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
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True


def run(store, graph_id, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. This tool takes graph_id and top_k.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if g.directed:
        return error(f"Graph '{graph_id}' is directed, and a minimum spanning tree is only defined for "
                     f"undirected graphs. Use an undirected graph such as 'lesmis' or 'karate'.")
    if g.number_of_nodes() == 0 or g.number_of_edges() == 0:
        return error(f"Graph '{graph_id}' has no edges, so it has no spanning tree.")

    # Kruskal: sort edges by (weight, u, v) so ties are broken deterministically.
    edges = []
    for u, v, w in g.edges():
        if u == v:
            continue  # self-loops never belong to a spanning tree
        a, b = (u, v) if u <= v else (v, u)
        edges.append((w, a, b))
    edges.sort()

    uf = _UnionFind(g.nodes())
    tree = []
    for w, a, b in edges:
        if uf.union(a, b):
            tree.append((w, a, b))
    total = round(sum(w for w, _, _ in tree), 6)
    n_nodes = g.number_of_nodes()
    n_components = n_nodes - len(tree)

    all_edges = [{"source": node_ref(g, a), "target": node_ref(g, b), "weight": round(w, 6)}
                 for w, a, b in tree]
    shown = all_edges[:k]
    result = {"total_weight": total, "num_tree_edges": len(tree), "num_nodes": n_nodes,
              "num_components": n_components, "edges_returned": len(shown),
              "edges": shown, "edges_note": "Edges are listed cheapest first (Kruskal order)."}
    while shown and len(json.dumps(result)) > MAX_RESULT_BYTES:
        shown = shown[:-1]
        result["edges"], result["edges_returned"] = shown, len(shown)

    desc = f"Minimum spanning {'tree' if n_components == 1 else 'forest'} of '{graph_id}'"
    sub_id = store.edge_subgraph(graph_id, [(a, b) for _, a, b in tree], desc)

    weight_note = "" if g.weighted else " (the graph is unweighted, so every edge counts as 1)"
    if n_components == 1:
        summary = (f"The minimum spanning tree of '{graph_id}' connects all {n_nodes} nodes with "
                   f"{len(tree)} edges and total weight {total}{weight_note}.")
    else:
        summary = (f"'{graph_id}' is disconnected ({n_components} components), so this is a minimum spanning "
                   f"forest: {len(tree)} edges, total weight {total}{weight_note}.")
    summary += f" Showing {len(shown)} of {len(tree)} edges; the full tree is registered as '{sub_id}'."
    return ok(result, summary, result_graph_id=sub_id)
