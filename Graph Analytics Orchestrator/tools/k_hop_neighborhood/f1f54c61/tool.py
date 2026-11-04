"""Find all nodes within k outgoing hops of a starting node. The returned subgraph is induced: it contains every original edge whose endpoints are both among the selected nodes."""

from graphkit.contract import check_node, check_top_k, error, get_graph, node_ref, ok

from collections import deque

def run(store, graph_id, node=None, k=2, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}.")
    err = check_node(g, node)
    if err:
        return err
    if isinstance(k, bool) or not isinstance(k, int) or k < 0:
        return error(f"k must be a non-negative integer; got {k!r}.")
    top_k, err = check_top_k(top_k)
    if err:
        return err

    # BFS computes the shortest outgoing-hop distance from the start and starting distance is 0
    distances = {node: 0}
    queue = deque([node])

    while queue:
        current = queue.popleft()
        current_distance = distances[current]

        if current_distance == k:
            continue

        # For directed graphs, follow outgoing edges only
        # For undirected graphs follow all edges
        for neighbour in g.out_neighbors(current):
            if neighbour not in distances:
                distances[neighbour] = current_distance + 1
                queue.append(neighbour)

    selected_nodes = sorted(distances, key=lambda n: (distances[n], n))

    # Limit displayed nodes to keep the output within the 8 KB limit while preserving the full neighborhood in the registered subgraph
    result = {
        "start_node": node_ref(g, node),
        "k": k,
        "top_k": top_k,
        "nodes": [
            node_ref(g, n, distance=distances[n])
            for n in selected_nodes[:top_k]
        ],
        "node_count": len(selected_nodes),
    }

    description = (
        f"Nodes within {k} outgoing hops of "
        f"{g.label(node)} in {graph_id}"
    )

    try:
        sub_id = store.subgraph(graph_id, selected_nodes, description)
    except (ValueError, KeyError) as exc:
        return error(f"Could not register neighbourhood subgraph: {exc}")

    summary = (
        f"Found {len(selected_nodes)} nodes within {k} outgoing hops "
        f"of '{g.label(node)}'."
    )

    return ok(result, summary, result_graph_id=sub_id)