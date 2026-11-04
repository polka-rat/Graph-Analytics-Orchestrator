"""Find a minimum-hop path with breadth-first search."""

from collections import deque

from graphkit.contract import check_node, error, get_graph, node_ref, ok


def run(store, graph_id, source=None, target=None, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(sorted(params))}.")
    err = check_node(g, source, "source")
    if err:
        return err
    err = check_node(g, target, "target")
    if err:
        return err

    parent = {source: None}
    queue = deque([source])
    while queue and target not in parent:
        node = queue.popleft()
        for neighbour in sorted(g.out_neighbors(node)):
            if neighbour not in parent:
                parent[neighbour] = node
                queue.append(neighbour)

    if target not in parent:
        direction = "following edge directions" if g.directed else "in the undirected graph"
        return error(
            f"No path exists from '{source}' to '{target}' {direction}. "
            "Check the node ids with lookup_node or try the reverse direction."
        )

    path = []
    node = target
    while node is not None:
        path.append(node)
        node = parent[node]
    path.reverse()
    hops = len(path) - 1
    result = {
        "source": node_ref(g, source),
        "target": node_ref(g, target),
        "path": [node_ref(g, node) for node in path],
        "hops": hops,
        "distance": hops,
    }
    wording = "directed" if g.directed else "undirected"
    summary = (
        f"The shortest {wording} path from {g.label(source)} ({source}) to "
        f"{g.label(target)} ({target}) uses {hops} hop{'s' if hops != 1 else ''}."
    )
    return ok(result, summary)
