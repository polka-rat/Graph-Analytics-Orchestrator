from collections import deque

from graphkit.contract import error, get_graph, node_ref, ok


def _components(nodes, adjacency):
    remaining = set(nodes)
    components = []
    while remaining:
        start = min(remaining)
        seen = {start}
        queue = deque([start])
        while queue:
            node = queue.popleft()
            for neighbor in sorted(adjacency[node]):
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)
        remaining.difference_update(seen)
        components.append(seen)
    return components


def _edge_betweenness(nodes, adjacency):
    scores = {}
    for source in sorted(nodes):
        stack = []
        predecessors = {node: [] for node in nodes}
        paths = dict.fromkeys(nodes, 0.0)
        paths[source] = 1.0
        distance = dict.fromkeys(nodes, -1)
        distance[source] = 0
        queue = deque([source])

        while queue:
            node = queue.popleft()
            stack.append(node)
            for neighbor in sorted(adjacency[node]):
                if distance[neighbor] < 0:
                    distance[neighbor] = distance[node] + 1
                    queue.append(neighbor)
                if distance[neighbor] == distance[node] + 1:
                    paths[neighbor] += paths[node]
                    predecessors[neighbor].append(node)

        dependency = dict.fromkeys(nodes, 0.0)
        while stack:
            node = stack.pop()
            if paths[node] == 0:
                continue
            coefficient = (1.0 + dependency[node]) / paths[node]
            for predecessor in predecessors[node]:
                contribution = paths[predecessor] * coefficient
                edge = tuple(sorted((predecessor, node)))
                scores[edge] = scores.get(edge, 0.0) + contribution
                dependency[predecessor] += contribution

    return {edge: value / 2.0 for edge, value in scores.items()}


def _modularity(g, communities):
    m = g.number_of_edges()
    if m == 0:
        return 0.0
    degree = {node: len(g.neighbors(node)) for node in g.nodes()}
    total = 0.0
    for community in communities:
        internal_edges = sum(
            1 for u, v, _ in g.edges() if u in community and v in community
        )
        degree_sum = sum(degree[node] for node in community)
        total += internal_edges / m - (degree_sum / (2 * m)) ** 2
    return total


def run(store, graph_id, num_communities=2, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(
            f"Unknown parameter(s): {', '.join(sorted(params))}. "
            "girvan_newman takes graph_id and num_communities."
        )
    if g.directed:
        return error(
            "girvan_newman requires an undirected graph. Choose an undirected graph with list_graphs."
        )
    if isinstance(num_communities, bool) or not isinstance(num_communities, int):
        return error("num_communities must be a whole number from 2 to 20.")
    if not 2 <= num_communities <= 20:
        return error("num_communities must be a whole number from 2 to 20.")
    nodes = g.nodes()
    if num_communities > len(nodes):
        return error(
            f"num_communities cannot exceed the {len(nodes)} nodes in graph '{graph_id}'. "
            "Choose a smaller value."
        )

    adjacency = {node: set(g.neighbors(node)) - {node} for node in nodes}
    communities = _components(nodes, adjacency)
    if len(communities) > num_communities:
        return error(
            f"Graph '{graph_id}' already has {len(communities)} connected components, more than "
            f"the requested {num_communities}. Request at least {len(communities)} communities."
        )

    while len(communities) < num_communities:
        scores = _edge_betweenness(nodes, adjacency)
        if not scores:
            return error(
                f"The graph has no remaining edges but only {len(communities)} communities. "
                "Choose a smaller num_communities."
            )
        highest = max(scores.values())
        edge = min(edge for edge, score in scores.items() if abs(score - highest) <= 1e-12)
        u, v = edge
        adjacency[u].discard(v)
        adjacency[v].discard(u)
        communities = _components(nodes, adjacency)

    ordered = sorted(communities, key=lambda group: (-len(group), min(group)))
    result = []
    for index, community in enumerate(ordered, 1):
        ordered_nodes = sorted(community)
        subgraph_id = store.subgraph(
            graph_id,
            ordered_nodes,
            f"Girvan-Newman community {index} of '{graph_id}'",
        )
        result.append(
            {
                "community": index,
                "size": len(ordered_nodes),
                "nodes": [node_ref(g, node) for node in ordered_nodes],
                "graph_id": subgraph_id,
            }
        )

    modularity = round(_modularity(g, ordered), 6)
    summary = (
        f"Girvan-Newman split graph '{graph_id}' into {len(result)} communities "
        f"with sizes {', '.join(str(item['size']) for item in result)} and modularity {modularity}."
    )
    return ok(
        {"communities": result, "modularity": modularity},
        summary,
        result_graph_id=result[0]["graph_id"],
    )
