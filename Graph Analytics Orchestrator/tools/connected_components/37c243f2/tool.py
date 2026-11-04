
"""Find connected components in an undirected graph."""

from graphkit.contract import error, get_graph, node_ref, ok


def run(store, graph_id: str, **params) -> dict:
    """Find connected components and register each as a subgraph."""

    if params:
        return error(f"Unknown parameter(s): {', '.join(sorted(params))}.")

    g, err = get_graph(store, graph_id)
    if err:
        return err

    if g.directed:
        return error("connected_components requires an undirected graph.")

    visited = set()
    components = []

    for start in sorted(g.nodes()):
        if start in visited:
            continue

        stack = [start]
        visited.add(start)
        component_nodes = []

        while stack:
            node = stack.pop()
            component_nodes.append(node)

            for neighbor in sorted(g.neighbors(node), reverse=True):
                if neighbor not in visited:
                    visited.add(neighbor)
                    stack.append(neighbor)

        component_nodes.sort()
        components.append(component_nodes)

    components.sort(key=lambda nodes: (-len(nodes), nodes[0]))

    result = []
    result_graph_id = None

    for index, nodes in enumerate(components, start=1):
        subgraph_id = store.subgraph(
            graph_id,
            nodes,
            f"Connected component {index} of graph '{graph_id}'"
        )

        result.append({
            "component": index,
            "size": len(nodes),
            "graph_id": subgraph_id,
            "nodes": [node_ref(g, node) for node in nodes]
        })

        if index == 1:
            result_graph_id = subgraph_id

    largest_size = len(components[0]) if components else 0

    summary = (
        f"The graph has {len(components)} connected component(s). "
        f"The largest component contains {largest_size} node(s), "
        f"out of {g.number_of_nodes()} total nodes."
    )

    return ok(result, summary, result_graph_id=result_graph_id)
