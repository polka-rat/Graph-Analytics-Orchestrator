"""Detect communities in an undirected graph using Girvan-Newman."""

from collections import deque

from graphkit.contract import check_top_k, error, get_graph, node_ref, ok


def _connected_components(adjacency):
    """Return connected components in deterministic order."""
    unseen = set(adjacency)
    components = []

    for start in sorted(adjacency):
        if start not in unseen:
            continue

        unseen.remove(start)
        queue = deque([start])
        component = []

        while queue:
            node = queue.popleft()
            component.append(node)

            for neighbour in sorted(adjacency[node]):
                if neighbour in unseen:
                    unseen.remove(neighbour)
                    queue.append(neighbour)

        components.append(tuple(sorted(component)))

    return sorted(components, key=lambda c: (-len(c), c))


def _edge_betweenness(adjacency):
    """Calculate unweighted edge betweenness using Brandes' algorithm."""
    scores = {}

    for u in adjacency:
        for v in adjacency[u]:
            if u < v:
                scores[(u, v)] = 0.0

    for source in sorted(adjacency):
        stack = []
        predecessors = {node: [] for node in adjacency}
        distance = {node: -1 for node in adjacency}
        path_count = {node: 0.0 for node in adjacency}

        distance[source] = 0
        path_count[source] = 1.0
        queue = deque([source])

        while queue:
            current = queue.popleft()
            stack.append(current)

            for neighbour in sorted(adjacency[current]):
                if distance[neighbour] == -1:
                    distance[neighbour] = distance[current] + 1
                    queue.append(neighbour)

                if distance[neighbour] == distance[current] + 1:
                    path_count[neighbour] += path_count[current]
                    predecessors[neighbour].append(current)

        dependency = {node: 0.0 for node in adjacency}

        while stack:
            node = stack.pop()

            if path_count[node] == 0:
                continue

            for predecessor in predecessors[node]:
                contribution = (
                    path_count[predecessor] / path_count[node]
                ) * (1.0 + dependency[node])

                edge = (
                    (predecessor, node)
                    if predecessor < node
                    else (node, predecessor)
                )

                scores[edge] += contribution
                dependency[predecessor] += contribution

    # Undirected paths are counted from both endpoints.
    return {
        edge: round(score / 2.0, 6)
        for edge, score in scores.items()
    }


def run(store, graph_id, top_k=10, num_communities=2, **params):
    """Detect communities by repeatedly removing high-betweenness edges."""
    if params:
        names = ", ".join(sorted(params))
        return error(
            f"Unknown parameter(s): {names}. "
            "Supported parameters are top_k and num_communities."
        )

    k, validation_error = check_top_k(top_k)
    if validation_error:
        return validation_error

    if (
        isinstance(num_communities, bool)
        or not isinstance(num_communities, int)
        or not 1 <= num_communities <= 100
    ):
        return error(
            "num_communities must be a whole number from 1 to 100."
        )

    graph, graph_error = get_graph(store, graph_id)
    if graph_error:
        return graph_error

    if graph.directed:
        return error(
            "Girvan-Newman requires an undirected graph. "
            "Choose an undirected graph."
        )

    nodes = sorted(graph.nodes())

    if not nodes:
        return ok([], f"Graph '{graph_id}' contains no nodes.")

    # This implementation treats every edge as unweighted.
    adjacency = {node: set() for node in nodes}

    for u, v, _weight in graph.edges():
        adjacency[u].add(v)
        adjacency[v].add(u)

    components = _connected_components(adjacency)

    # Recalculate edge betweenness after every edge removal.
    while len(components) < num_communities:
        scores = _edge_betweenness(adjacency)

        if not scores:
            break

        highest_score = max(scores.values())
        tied_edges = [
            edge
            for edge, score in scores.items()
            if abs(score - highest_score) <= 1e-6
        ]

        # Deterministic tie-breaking using node IDs.
        edge = min(tied_edges)
        u, v = edge

        adjacency[u].remove(v)
        adjacency[v].remove(u)

        components = _connected_components(adjacency)

    selected = components[:k]
    results = []
    largest_subgraph_id = None

    for index, community in enumerate(selected, start=1):
        description = (
            f"Community {index} detected by Girvan-Newman "
            f"on graph '{graph_id}'"
        )

        try:
            subgraph_id = store.subgraph(
                graph_id, community, description
            )
        except (KeyError, ValueError) as exc:
            return error(
                f"Could not register community {index}: {exc}. "
                "Check that the source graph is valid."
            )

        if largest_subgraph_id is None:
            largest_subgraph_id = subgraph_id

        results.append({
            "community": index,
            "graph_id": subgraph_id,
            "size": len(community),
            "nodes": [
                node_ref(graph, node)
                for node in community[:k]
            ],
            "omitted_nodes": max(0, len(community) - k),
        })

    if components:
        largest_size = len(components[0])
    else:
        largest_size = 0

    summary = (
        f"Girvan-Newman detected {len(components)} communities "
        f"in graph '{graph_id}' for a target of {num_communities}. "
        f"Returning {len(results)} communities; the largest "
        f"contains {largest_size} nodes."
    )

    return ok(
        results,
        summary,
        result_graph_id=largest_subgraph_id,
    )
