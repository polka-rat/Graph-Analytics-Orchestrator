
"""Detect communities using the Girvan-Newman algorithm."""

from collections import deque
import math

from graphkit.contract import error, get_graph, node_ref, ok


def _connected_components(nodes, adjacency):
    """Return connected components, with nodes sorted deterministically."""
    unseen = set(nodes)
    components = []

    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        component = []

        while queue:
            current = queue.popleft()
            component.append(current)

            for neighbor in sorted(adjacency[current]):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)

        components.append(sorted(component))

    components.sort(key=lambda component: component[0])
    return components


def _edge_betweenness(nodes, adjacency):
    """
    Calculate unweighted edge betweenness using Brandes' algorithm.

    The graph is undirected. Scores are divided by two because each
    undirected shortest path is counted from both source directions.
    """
    scores = {
        (u, v): 0.0
        for u in nodes
        for v in sorted(adjacency[u])
        if u < v
    }

    for source in sorted(nodes):
        predecessors = {n: [] for n in nodes}
        shortest_path_count = {n: 0.0 for n in nodes}
        distance = {n: -1 for n in nodes}

        shortest_path_count[source] = 1.0
        distance[source] = 0

        queue = deque([source])
        stack = []

        # BFS: find shortest distances and count shortest paths.
        while queue:
            current = queue.popleft()
            stack.append(current)

            for neighbor in sorted(adjacency[current]):
                if distance[neighbor] == -1:
                    distance[neighbor] = distance[current] + 1
                    queue.append(neighbor)

                if distance[neighbor] == distance[current] + 1:
                    shortest_path_count[neighbor] += (
                        shortest_path_count[current]
                    )
                    predecessors[neighbor].append(current)

        # Back-propagate shortest-path contributions.
        dependency = {n: 0.0 for n in nodes}

        while stack:
            target = stack.pop()

            for predecessor in predecessors[target]:
                contribution = (
                    shortest_path_count[predecessor]
                    / shortest_path_count[target]
                ) * (1.0 + dependency[target])

                edge = (
                    min(predecessor, target),
                    max(predecessor, target),
                )
                scores[edge] += contribution
                dependency[predecessor] += contribution

    for edge in scores:
        scores[edge] /= 2.0

    return scores


def run(store, graph_id, communities=2, **params):
    """Find communities by repeatedly removing high-betweenness edges."""
    g, err = get_graph(store, graph_id)
    if err:
        return err

    if params:
        names = ", ".join(sorted(params))
        return error(
            f"Unknown parameter(s): {names}. "
            "Supported parameters are graph_id and communities."
        )

    if isinstance(communities, bool) or not isinstance(communities, int):
        return error(
            "Parameter 'communities' must be an integer greater than or equal to 1."
        )

    if communities < 1:
        return error(
            "Parameter 'communities' must be at least 1."
        )

    if g.directed:
        return error(
            "Girvan-Newman requires an undirected graph. "
            "Please select an undirected graph."
        )

    nodes = sorted(g.nodes())

    if not nodes:
        return error("Cannot detect communities in an empty graph.")

    if communities > len(nodes):
        return error(
            f"Requested {communities} communities, but the graph has "
            f"only {len(nodes)} nodes. Choose a target no greater than "
            f"{len(nodes)}."
        )

    # Copy the graph structure; never modify the original graph.
    adjacency = {n: set() for n in nodes}

    for u, v, _weight in g.edges():
        if u != v:
            adjacency[u].add(v)
            adjacency[v].add(u)

    removed_edges = []
    components = _connected_components(nodes, adjacency)

    # Removing edges cannot merge components, so stop if the requested
    # target has already been reached or exceeded.
    while len(components) < communities:
        scores = _edge_betweenness(nodes, adjacency)

        if not scores:
            break

        highest_score = max(scores.values())

        # Treat tiny floating-point differences as ties.
        tied_edges = [
            edge
            for edge, score in scores.items()
            if math.isclose(
                score, highest_score, rel_tol=1e-12, abs_tol=1e-12
            )
        ]

        # Edges are normalized as (smaller node ID, larger node ID).
        edge = min(tied_edges)

        u, v = edge
        removed_edges.append({
            "source": node_ref(g, u),
            "target": node_ref(g, v),
            "betweenness": round(scores[edge], 6),
        })

        adjacency[u].remove(v)
        adjacency[v].remove(u)

        components = _connected_components(nodes, adjacency)

    # Register every resulting community as a subgraph.
    community_results = []
    for index, component in enumerate(components, start=1):
        description = (
            f"Girvan-Newman community {index} from graph {graph_id}"
        )
        subgraph_id = store.subgraph(graph_id, component, description)

        community_results.append({
            "community": index,
            "graph_id": subgraph_id,
            "size": len(component),
            "nodes": [node_ref(g, n) for n in component],
        })

    # The largest community's subgraph is the primary result graph.
    largest = min(
        community_results,
        key=lambda item: (-item["size"], item["nodes"][0]["id"]),
    )

    result = {
        "number_of_communities": len(community_results),
        "communities": community_results,
        "removed_edges": removed_edges,
    }

    summary = (
        f"Found {len(community_results)} communities in graph "
        f"{graph_id}, removing {len(removed_edges)} edges. "
        f"The largest community contains {largest['size']} nodes."
    )

    return ok(
        result,
        summary,
        result_graph_id=largest["graph_id"],
    )
