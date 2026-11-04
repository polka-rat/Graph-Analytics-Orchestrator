"""Find a maximum-cardinality matching in a bipartite graph with Hopcroft-Karp."""

from collections import deque
import json

from graphkit.contract import MAX_OUTPUT_BYTES, error, get_graph, node_ref, ok


def _partition(graph: object) -> tuple[list[str], list[str]] | None:
    """Return a deterministic bipartition, or None if the graph is not bipartite."""
    nodes = sorted(graph.nodes())
    neighbors = {node: set(graph.undirected_neighbors(node)) for node in nodes}

    # Prefer the dataset's semantic partition when it is complete and consistent.
    sides = {node: graph.node_attrs(node).get("side") for node in nodes}
    distinct_sides = set(sides.values())
    if nodes and None not in distinct_sides and len(distinct_sides) == 2:
        side_values = sorted(distinct_sides)
        consistent = all(
            node not in neighbors[node]
            and all(sides[neighbor] != sides[node] for neighbor in neighbors[node])
            for node in nodes
        )
        if consistent:
            # Give the familiar student/project names their natural orientation.
            if set(side_values) == {"project", "student"}:
                left_side, right_side = "student", "project"
            else:
                left_side, right_side = side_values
            return (
                [node for node in nodes if sides[node] == left_side],
                [node for node in nodes if sides[node] == right_side],
            )

    # Otherwise derive the two sides by a deterministic BFS coloring. Each
    # disconnected component starts at its smallest node on the left side.
    color: dict[str, int] = {}
    for root in nodes:
        if root in color:
            continue
        color[root] = 0
        queue = deque([root])
        while queue:
            current = queue.popleft()
            for neighbor in sorted(neighbors[current]):
                if neighbor == current:
                    return None
                expected = 1 - color[current]
                if neighbor in color:
                    if color[neighbor] != expected:
                        return None
                else:
                    color[neighbor] = expected
                    queue.append(neighbor)
    return (
        [node for node in nodes if color[node] == 0],
        [node for node in nodes if color[node] == 1],
    )


def _hopcroft_karp(left: list[str], right: list[str], adjacency: dict[str, list[str]]) -> dict[str, str]:
    """Return a maximum matching from left nodes to right nodes."""
    pair_left: dict[str, str | None] = {node: None for node in left}
    pair_right: dict[str, str | None] = {node: None for node in right}
    distance: dict[str, int] = {}
    infinity = len(left) + len(right) + 1
    shortest_augmenting_length = infinity

    def build_layers() -> bool:
        nonlocal shortest_augmenting_length
        queue = deque()
        for node in left:
            if pair_left[node] is None:
                distance[node] = 0
                queue.append(node)
            else:
                distance[node] = infinity

        shortest_augmenting_length = infinity
        while queue:
            node = queue.popleft()
            if distance[node] + 1 > shortest_augmenting_length:
                continue
            for neighbor in adjacency[node]:
                paired_left = pair_right[neighbor]
                if paired_left is None:
                    shortest_augmenting_length = min(
                        shortest_augmenting_length, distance[node] + 1
                    )
                elif (
                    distance[node] + 1 < shortest_augmenting_length
                    and distance[paired_left] == infinity
                ):
                    distance[paired_left] = distance[node] + 1
                    queue.append(paired_left)
        return shortest_augmenting_length != infinity

    def augment(node: str) -> bool:
        for neighbor in adjacency[node]:
            paired_left = pair_right[neighbor]
            if paired_left is None:
                if distance[node] + 1 != shortest_augmenting_length:
                    continue
            elif distance.get(paired_left, infinity) != distance[node] + 1 or not augment(paired_left):
                continue
            pair_left[node] = neighbor
            pair_right[neighbor] = node
            return True
        distance[node] = infinity
        return False

    while build_layers():
        for node in left:
            if pair_left[node] is None:
                augment(node)

    return {node: neighbor for node, neighbor in pair_left.items() if neighbor is not None}


def run(store, graph_id: str, **params) -> dict:
    graph, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(
            f"Unknown parameter(s): {', '.join(params)}. "
            "bipartite_matching takes only graph_id."
        )
    if graph.directed:
        return error(
            f"Graph '{graph_id}' is directed. Hopcroft–Karp matching requires an undirected "
            "bipartite graph; use an undirected eligibility graph instead."
        )

    partition = _partition(graph)
    if partition is None:
        return error(
            f"Graph '{graph_id}' is not bipartite (it contains an odd cycle or self-loop). "
            "Use an undirected graph whose edges only connect the two groups."
        )

    left, right = partition
    right_set = set(right)
    adjacency = {
        node: sorted(neighbor for neighbor in graph.undirected_neighbors(node) if neighbor in right_set)
        for node in left
    }
    matching = _hopcroft_karp(left, right, adjacency)

    # The projects dataset has meaningful group names; use them directly.
    node_sides = {node: graph.node_attrs(node).get("side") for node in graph.nodes()}
    has_student_project_sides = (
        bool(node_sides)
        and set(node_sides.values()) == {"student", "project"}
        and all(node_sides[u] != node_sides[v] for u, v, _ in graph.edges())
    )
    if has_student_project_sides:
        pairs = [
            {"student": node_ref(graph, student), "project": node_ref(graph, project)}
            for student, project in sorted(matching.items())
        ]
        matched_students = set(matching)
        matched_projects = set(matching.values())
        unmatched_left = [node_ref(graph, node) for node in left if node not in matched_students]
        unmatched_right = [node_ref(graph, node) for node in right if node not in matched_projects]
        result = {
            "matching_size": len(matching),
            "matching": pairs,
            "unmatched_students": unmatched_left,
            "unmatched_projects": unmatched_right,
        }
        summary = (
            f"A maximum matching assigns {len(matching)} of {len(left)} students to "
            f"{len(right)} projects; no student or project appears more than once."
        )
    else:
        pairs = [
            {"left": node_ref(graph, node), "right": node_ref(graph, neighbor)}
            for node, neighbor in sorted(matching.items())
        ]
        matched_left = set(matching)
        matched_right = set(matching.values())
        result = {
            "matching_size": len(matching),
            "matching": pairs,
            "unmatched_left": [node_ref(graph, node) for node in left if node not in matched_left],
            "unmatched_right": [node_ref(graph, node) for node in right if node not in matched_right],
        }
        summary = (
            f"A maximum matching pairs {len(matching)} nodes across the two sides "
            f"of the bipartite graph; no node appears more than once."
        )

    output = ok(result, summary)
    if len(json.dumps(output, ensure_ascii=False).encode("utf-8")) > MAX_OUTPUT_BYTES:
        return error(
            "The complete matching is too large for the 8 KB response limit. "
            "Use a smaller bipartite graph."
        )
    return output
