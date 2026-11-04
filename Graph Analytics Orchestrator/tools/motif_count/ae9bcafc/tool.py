"""Count three-node motifs without external graph libraries."""

from graphkit.contract import error, get_graph, ok


def _projection_counts(nodes, neighbours):
    rank = {node: index for index, node in enumerate(nodes)}
    triangles = 0
    for left in nodes:
        for right in neighbours[left]:
            if rank[right] <= rank[left]:
                continue
            triangles += sum(rank[third] > rank[right] for third in neighbours[left] & neighbours[right])
    triplets = sum(len(neighbours[node]) * (len(neighbours[node]) - 1) // 2 for node in nodes)
    return triangles, triplets - 3 * triangles


def run(store, graph_id, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(sorted(params))}.")

    nodes = sorted(g.nodes())
    outgoing = {
        node: {neighbour for neighbour in g.out_neighbors(node) if neighbour != node}
        for node in nodes
    }
    projection = {node: set(outgoing[node]) for node in nodes}
    if g.directed:
        for node in nodes:
            projection[node].update(neighbour for neighbour in g.in_neighbors(node) if neighbour != node)

    triangles, open_triads = _projection_counts(nodes, projection)
    result = {
        "graph_type": "directed" if g.directed else "undirected",
        "node_count": g.number_of_nodes(),
        "edge_count": g.number_of_edges(),
        "triangles": triangles,
        "open_triads": open_triads,
    }

    if g.directed:
        incoming = {
            node: {neighbour for neighbour in g.in_neighbors(node) if neighbour != node}
            for node in nodes
        }
        feed_forward = 0
        cycle_steps = 0
        reciprocal_pairs = 0
        for source in nodes:
            for middle in outgoing[source]:
                feed_forward += len((outgoing[source] & outgoing[middle]) - {source, middle})
                cycle_steps += len((outgoing[middle] & incoming[source]) - {source, middle})
                if source < middle and source in outgoing[middle]:
                    reciprocal_pairs += 1
        result.update(
            {
                "feed_forward_loops": feed_forward,
                "directed_3_cycles": cycle_steps // 3,
                "reciprocal_pairs": reciprocal_pairs,
            }
        )
        summary = (
            f"Graph '{graph_id}' has {triangles} triangle(s) in its undirected projection, "
            f"{open_triads} open triad(s), {feed_forward} feed-forward loop(s), "
            f"{cycle_steps // 3} directed 3-cycle(s), and {reciprocal_pairs} reciprocal pair(s)."
        )
    else:
        summary = f"Graph '{graph_id}' has {triangles} triangle(s) and {open_triads} open triad(s)."

    return ok(result, summary)
