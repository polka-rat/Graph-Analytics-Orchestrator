"""Compute a minimum spanning tree or forest using Kruskal's algorithm.

Rules (the validator checks them):
- Implement the algorithm yourself: standard library, NumPy and graphkit only.
- Get graphs only from the store; never open files, print, or use the network.
- Never crash: return error("what went wrong and how to fix it") instead.
- Return every node as node_ref(g, node, ...), so it has both an id and a label.
- Keep the output under 8 KB: respect top_k.
- Be deterministic: same input, same output. Randomised algorithms take a `seed` parameter (default 0).
"""
from graphkit.contract import check_node, check_top_k, error, get_graph, node_ref, ok


def run(store, graph_id, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(sorted(params))}.")

    k, err = check_top_k(top_k)
    if err:
        return err

    # TODO: your algorithm. Useful Graph methods:
    #   g.nodes(), g.number_of_nodes(), g.number_of_edges(), g.directed, g.weighted
    #   g.out_neighbors(n), g.in_neighbors(n), g.undirected_neighbors(n)   -> {neighbour: weight}
    #   g.edges() -> (u, v, weight), g.weight(u, v), g.label(n), g.node_attrs(n)
    if g.directed:
        return error(
            "Minimum spanning trees require an undirected graph. "
            "Choose an undirected graph such as 'karate' or 'lesmis'."
        )

    nodes = list(g.nodes())
    parent = {node: node for node in nodes}
    rank = {node: 0 for node in nodes}

    def find(node):
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(a, b):
        root_a = find(a)
        root_b = find(b)

        if root_a == root_b:
            return False

        if rank[root_a] < rank[root_b]:
            root_a, root_b = root_b, root_a

        parent[root_b] = root_a
        if rank[root_a] == rank[root_b]:
            rank[root_a] += 1

        return True

    edges = []
    for u, v, weight in g.edges():
        if u == v:
            continue

        edge_weight = float(weight) if g.weighted else 1.0
        # Normalize endpoints for deterministic tie-breaking.
        a, b = sorted((u, v), key=str)
        edges.append((edge_weight, str(a), str(b), a, b))

    edges.sort(key=lambda edge: (edge[0], edge[1], edge[2]))

    selected = []
    total_weight = 0.0

    for weight, _, __, u, v in edges:
        if union(u, v):
            selected.append((u, v, weight))
            total_weight += weight

    # Sort selected edges deterministically for the returned result.
    selected.sort(
        key=lambda edge: (
            edge[2],
            str(min(edge[0], edge[1], key=str)),
            str(max(edge[0], edge[1], key=str)),
        )
    )

    component_roots = {find(node) for node in nodes}
    component_count = len(component_roots)
    is_connected = len(nodes) == 0 or component_count == 1

    result_edges = [
        {
            "source": node_ref(g, u),
            "target": node_ref(g, v),
            "weight": round(weight, 6),
        }
        for u, v, weight in selected[:k]
    ]

    result = {
        "graph_id": graph_id,
        "number_of_nodes": len(nodes),
        "number_of_edges": g.number_of_edges(),
        "selected_edge_count": len(selected),
        "total_weight": round(total_weight, 6),
        "is_spanning_tree": is_connected,
        "component_count": component_count,
        "edges": result_edges,
        "edges_truncated": len(selected) > k,
    }

    summary = (
        f"Minimum spanning {'tree' if is_connected else 'forest'} for "
        f"'{graph_id}': {len(nodes)} nodes, {len(selected)} selected edges, "
        f"total weight {round(total_weight, 6)}, "
        f"{component_count} component(s)."
    )

    result_graph_id = None
    if selected:
        result_graph_id = store.edge_subgraph(
            graph_id,
            [(u, v) for u, v, _ in selected],
            f"Minimum spanning forest of '{graph_id}'",
        )

    return ok(result, summary, result_graph_id=result_graph_id)

    # A tool that produces a node set or subgraph (marked with an arrow in the menu) registers it:
    #     sub_id = store.subgraph(graph_id, nodes, "Largest community of 'karate'")
    #     return ok(result, summary, result_graph_id=sub_id)
    # If it produces several node sets (e.g. communities), register each one, put its id in that
    # entry of the result as "graph_id", and return the largest one's id as result_graph_id.
