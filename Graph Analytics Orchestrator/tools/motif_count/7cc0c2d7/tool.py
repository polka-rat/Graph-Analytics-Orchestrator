"""Count triangle motifs in a graph."""

from graphkit.contract import error, get_graph, ok


def run(store, graph_id, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err

    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}.")

    nodes = g.nodes()

    # Build undirected adjacency sets so directed edges are treated
    # as connections regardless of their direction.
    adjacency = {node: set() for node in nodes}

    for u, v, _ in g.edges():
        if u != v:
            adjacency[u].add(v)
            adjacency[v].add(u)

    # Count each triangle once by considering ordered node indices.
    triangles = 0

    for i, u in enumerate(nodes):
        for v in nodes[i + 1:]:
            if v not in adjacency[u]:
                continue

            for w in nodes:
                if w <= v:
                    continue
                if w in adjacency[u] and w in adjacency[v]:
                    triangles += 1

    result = {
        "triangle_count": triangles,
        "node_count": len(nodes),
        "edge_count": g.number_of_edges(),
    }

    return ok(
        result,
        f"The graph contains {triangles} triangle motifs among {len(nodes)} nodes."
    )
