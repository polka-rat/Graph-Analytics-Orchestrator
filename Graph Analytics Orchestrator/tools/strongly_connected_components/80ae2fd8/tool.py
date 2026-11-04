"""Find strongly connected components in a directed graph using Kosaraju's algorithm."""

from graphkit.contract import check_top_k, error, get_graph, node_ref, ok

def find_strongly_connected_components(g):
    """Return all strongly connected components deterministically."""
    nodes = sorted(g.nodes())
    visited = set()
    finish_order = []

    # First pass: iterative DFS on outgoing edges.
    # Each stack frame keeps an iterator so finishing order is correct.
    for start in nodes:
        if start in visited:
            continue

        visited.add(start)
        stack = [(start, iter(sorted(g.out_neighbors(start))))]

        while stack:
            node, neighbors = stack[-1]

            try:
                neighbor = next(neighbors)
            except StopIteration:
                finish_order.append(node)
                stack.pop()
                continue

            if neighbor not in visited:
                visited.add(neighbor)
                stack.append(
                    (neighbor, iter(sorted(g.out_neighbors(neighbor))))
                )

    # Second pass: DFS on incoming edges in reverse finishing order.
    visited.clear()
    components = []

    for start in reversed(finish_order):
        if start in visited:
            continue

        component = []
        stack = [start]
        visited.add(start)

        while stack:
            node = stack.pop()
            component.append(node)

            for neighbor in sorted(g.in_neighbors(node), reverse=True):
                if neighbor not in visited:
                    visited.add(neighbor)
                    stack.append(neighbor)

        components.append(sorted(component))

    # Stable ordering by the smallest node ID in each component.
    components.sort(key=lambda component: component[0] if component else "")

    return components


def run(store, graph_id, **params):
    """Return a bounded, deterministic summary of strongly connected components."""

    unknown = set(params) - {"top_k"}
    if unknown:
        return error(
            f"Unknown parameter(s): {', '.join(sorted(unknown))}. "
            "Supported parameter: top_k (positive integer)."
        )

    top_k, validation_error = check_top_k(params.get("top_k", 10))
    if validation_error:
        return validation_error
    g, err = get_graph(store, graph_id)
    if err:
        return err

    if not g.directed:
        return error(
            f"Graph '{graph_id}' is undirected. "
            "strongly_connected_components requires a directed graph."
        )

    components = find_strongly_connected_components(g)
    selected = components[:top_k]

    result = {
        "graph_id": graph_id,
        "number_of_components": len(components),
        "returned_components": len(selected),
        "omitted_components": max(0, len(components) - len(selected)),
        "components": [
            {
                "component_id": index,
                "size": len(component),
                "nodes": [node_ref(g, node) for node in component[:top_k]],
                "omitted_nodes": max(0, len(component) - top_k),
            }
            for index, component in enumerate(selected, start=1)
        ],
    }

    summary = (
        f"Graph '{graph_id}' has {len(components)} strongly connected "
        f"component(s) across {g.number_of_nodes()} nodes. "
        f"Showing {len(selected)} component(s); top_k={top_k} limits "
        "the number of components and the number of node references "
        "shown per component."
    )

    return ok(result, summary)
