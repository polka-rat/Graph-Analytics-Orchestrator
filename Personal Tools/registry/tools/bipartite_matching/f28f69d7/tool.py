"""Find a maximum-cardinality matching in a bipartite graph."""

from collections import deque

from graphkit.contract import check_top_k, error, get_graph, node_ref, ok


def run(store, graph_id, top_k=10, **params):
    """Return a deterministic maximum matching using Hopcroft-Karp."""
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}.")
    k, err = check_top_k(top_k)
    if err:
        return err

    color = {}
    for start in sorted(g.nodes()):
        if start in color:
            continue
        color[start] = 0
        queue = deque([start])
        while queue:
            node = queue.popleft()
            for neighbor in sorted(g.undirected_neighbors(node)):
                if neighbor == node:
                    return error("The graph is not bipartite because it contains a self-loop.")
                if neighbor not in color:
                    color[neighbor] = 1 - color[node]
                    queue.append(neighbor)
                elif color[neighbor] == color[node]:
                    return error(
                        "The graph is not bipartite. Use a graph whose nodes can be split into two groups "
                        "with edges only between the groups."
                    )

    left = sorted(node for node, node_color in color.items() if node_color == 0)
    right = {node for node, node_color in color.items() if node_color == 1}

    adjacency = {
        node: sorted(neighbor for neighbor in g.undirected_neighbors(node) if neighbor in right)
        for node in left
    }
    pair_left = {node: None for node in left}
    pair_right = {node: None for node in right}
    distance = {}

    def bfs():
        queue = deque()
        shortest_augmenting_length = None
        for node in left:
            if pair_left[node] is None:
                distance[node] = 0
                queue.append(node)
            else:
                distance[node] = None

        while queue:
            node = queue.popleft()
            if shortest_augmenting_length is not None and distance[node] >= shortest_augmenting_length:
                continue
            for neighbor in adjacency[node]:
                matched_node = pair_right[neighbor]
                if matched_node is None:
                    shortest_augmenting_length = distance[node] + 1
                elif distance[matched_node] is None:
                    distance[matched_node] = distance[node] + 1
                    queue.append(matched_node)
        return shortest_augmenting_length is not None

    def dfs(node):
        for neighbor in adjacency[node]:
            matched_node = pair_right[neighbor]
            if matched_node is None or (
                distance[matched_node] == distance[node] + 1 and dfs(matched_node)
            ):
                pair_left[node] = neighbor
                pair_right[neighbor] = node
                return True
        distance[node] = None
        return False

    while bfs():
        for node in left:
            if pair_left[node] is None:
                dfs(node)

    matches = [(node, pair_left[node]) for node in left if pair_left[node] is not None]
    result = {
        "matches": [
            {"left": node_ref(g, left_node), "right": node_ref(g, right_node)}
            for left_node, right_node in matches[:k]
        ],
        "matching_size": len(matches),
        "truncated": len(matches) > k,
    }
    summary = f"Found a maximum matching of {len(matches)} pair(s) in '{graph_id}'."
    return ok(result, summary)
