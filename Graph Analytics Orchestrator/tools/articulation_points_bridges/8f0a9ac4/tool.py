"""
Find nodes and edges whose removal disconnects a graph.
Return articulation points and bridges using Tarjan's depth-first search.
"""

from graphkit.contract import check_top_k, error, get_graph, node_ref, ok


def run(store, graph_id, top_k=10, **params):
    
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}.")
    k, err = check_top_k(top_k)
    if err:
        return err

    discovery = {}
    low = {}
    parent = {}
    articulation_points = set()
    bridges = set()
    clock = 0

    def visit(node):
        nonlocal clock
        discovery[node] = clock
        low[node] = clock
        clock += 1
        children = 0

        for neighbor in sorted(g.undirected_neighbors(node)):
            if neighbor not in discovery:
                parent[neighbor] = node
                children += 1
                visit(neighbor)
                low[node] = min(low[node], low[neighbor])

                if parent[node] is None and children > 1:
                    articulation_points.add(node)
                if parent[node] is not None and low[neighbor] >= discovery[node]:
                    articulation_points.add(node)
                if low[neighbor] > discovery[node]:
                    bridges.add(tuple(sorted((node, neighbor))))
            elif neighbor != parent[node]:
                low[node] = min(low[node], discovery[neighbor])

    for node in sorted(g.nodes()):
        if node not in discovery:
            parent[node] = None
            visit(node)

    ordered_points = sorted(articulation_points)
    ordered_bridges = sorted(bridges)
    result = {
        "articulation_points": [node_ref(g, node) for node in ordered_points[:k]],
        "bridges": [
            {"source": node_ref(g, source), "target": node_ref(g, target)}
            for source, target in ordered_bridges[:k]
        ],
        "total_articulation_points": len(ordered_points),
        "total_bridges": len(ordered_bridges),
        "truncated": len(ordered_points) > k or len(ordered_bridges) > k,
    }
    summary = (
        f"Found {len(ordered_points)} articulation point(s) and "
        f"{len(ordered_bridges)} bridge(s) in '{graph_id}'."
    )
    return ok(result, summary)
