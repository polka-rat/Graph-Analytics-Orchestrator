"""Find a fewest-hop path between two nodes with breadth-first search."""
from collections import deque

from graphkit.contract import check_node, error, get_graph, node_ref, ok


def _bfs_path(graph, source: str, target: str) -> list[str] | None:
    """Return a deterministic shortest path, following edge direction when present."""
    if source == target:
        return [source]

    parents: dict[str, str | None] = {source: None}
    queue = deque([source])

    while queue:
        current = queue.popleft()
        # Sorting neighbors makes the chosen path deterministic when several
        # routes have the same number of edges.
        for neighbor in sorted(graph.out_neighbors(current)):
            if neighbor in parents:
                continue
            parents[neighbor] = current
            if neighbor == target:
                path = [target]
                while path[-1] != source:
                    path.append(parents[path[-1]])
                path.reverse()
                return path
            queue.append(neighbor)

    return None


def run(store, graph_id: str, source: str = None, target: str = None, **params) -> dict:
    graph, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(
            f"Unknown parameter(s): {', '.join(params)}. "
            "shortest_path_unweighted takes graph_id, source, and target."
        )

    err = check_node(graph, source, "source")
    if err:
        return err
    err = check_node(graph, target, "target")
    if err:
        return err

    path = _bfs_path(graph, source, target)
    if path is None:
        direction = "directed " if graph.directed else ""
        return error(
            f"No {direction}path exists from '{source}' to '{target}' in graph "
            f"'{graph_id}'. Check the edge direction or choose connected nodes."
        )

    hops = len(path) - 1
    refs = [node_ref(graph, node) for node in path]
    hop_word = "hop" if hops == 1 else "hops"
    summary = (
        f"The fewest-hop path from {graph.label(source)} ({source}) to "
        f"{graph.label(target)} ({target}) uses {hops} {hop_word}."
    )
    return ok({"path": refs, "hops": hops}, summary)
