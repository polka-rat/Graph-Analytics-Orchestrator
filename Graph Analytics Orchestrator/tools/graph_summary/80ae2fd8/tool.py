"""Summarize the basic structural properties of a graph."""

from graphkit.contract import error, get_graph, ok


def count_connected_components(g):
    """Count weakly connected components using breadth-first search."""
    visited = set()
    component_count = 0

    for node in g.nodes():
        if node in visited:
            continue

        component_count += 1
        queue = [node]
        visited.add(node)
        head = 0

        while head < len(queue):
            current = queue[head]
            head += 1

            for neighbor in g.undirected_neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

    return component_count


def shortest_path_distances(g, start):
    """Calculate shortest-path distances from start using BFS."""
    distances = {start: 0}
    queue = [start]
    head = 0

    while head < len(queue):
        current = queue[head]
        head += 1

        for neighbor in g.undirected_neighbors(current):
            if neighbor not in distances:
                distances[neighbor] = distances[current] + 1
                queue.append(neighbor)

    return distances


def graph_eccentricities(g):
    """Calculate each node eccentricity for a connected, undirected graph."""
    nodes = list(g.nodes())
    eccentricities = {}

    for node in nodes:
        distances = shortest_path_distances(g, node)
        if len(distances) != len(nodes):
            return None
        eccentricities[node] = max(distances.values(), default=0)

    return eccentricities


def average_shortest_path_length(g):
    """Calculate average shortest-path length for a connected graph."""
    nodes = list(g.nodes())
    if len(nodes) < 2:
        return 0.0

    total_distance = 0
    pair_count = 0

    for i, node in enumerate(nodes):
        distances = shortest_path_distances(g, node)
        if len(distances) != len(nodes):
            return None
        for other in nodes[i + 1:]:
            total_distance += distances[other]
            pair_count += 1

    return total_distance / pair_count if pair_count else 0.0


def run(store, graph_id, **params):
    """Return basic structural statistics for the requested graph."""

    if params:
        return error(
            f"Unknown parameter(s): {', '.join(sorted(params))}. "
            "Provide only graph_id."
        )

    g, err = get_graph(store, graph_id)
    if err:
        return err

    number_of_nodes = g.number_of_nodes()
    number_of_edges = g.number_of_edges()
    connected_components_count = count_connected_components(g)

    if number_of_nodes < 2:
        density = 0.0
    elif g.directed:
        density = number_of_edges / (
            number_of_nodes * (number_of_nodes - 1)
        )
    else:
        density = (
            2 * number_of_edges
            / (number_of_nodes * (number_of_nodes - 1))
        )

    supports_path_metrics = (
        not g.directed
        and not g.weighted
        and connected_components_count == 1
    )

    if supports_path_metrics:
        eccentricities = graph_eccentricities(g)
        diameter = max(eccentricities.values(), default=0)
        radius = min(eccentricities.values(), default=0)
        average_path_length = average_shortest_path_length(g)
    else:
        diameter = None
        radius = None
        average_path_length = None

    result = {
        "graph_id": graph_id,
        "number_of_nodes": number_of_nodes,
        "number_of_edges": number_of_edges,
        "directed": g.directed,
        "weighted": g.weighted,
        "density": round(density, 6),
        "connected_components_count": connected_components_count,
        "diameter": diameter,
        "radius": radius,
        "average_shortest_path_length": (
            round(average_path_length, 6)
            if average_path_length is not None
            else None
        ),
    }

    graph_type = "directed" if g.directed else "undirected"
    weight_type = "weighted" if g.weighted else "unweighted"
    article = "a" if g.directed else "an"

    summary = (
        f"Graph '{graph_id}' is {article} {graph_type}, "
        f"{weight_type} graph with {number_of_nodes} nodes, "
        f"{number_of_edges} edges, density {result['density']}, "
        f"and {connected_components_count} connected component(s)."
    )

    if supports_path_metrics:
        summary += (
            f" Its diameter is {diameter}, radius is {radius}, "
            f"and average shortest-path length is "
            f"{result['average_shortest_path_length']}."
        )
    else:
        summary += (
            " Path metrics are unavailable under the current "
            "implementation's assumptions: connected, undirected, "
            "and unweighted."
        )

    if g.directed:
        summary += " Components are counted using weak connectivity."

    return ok(result, summary)
