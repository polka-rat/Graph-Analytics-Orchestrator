"""Extracts the ego network (induced subgraph centered on a focal node).

The ego network includes the focal node (the ego) and all neighbours (alters)
within a specified radius of hops, along with all edges between these nodes.
The induced subgraph is registered in the GraphStore and returned via result_graph_id.
"""
from __future__ import annotations

from collections import deque
import json

from graphkit.contract import (
    MAX_OUTPUT_BYTES,
    check_node,
    check_top_k,
    error,
    get_graph,
    node_ref,
    ok,
)


def run(
    store,
    graph_id: str,
    node: str = None,
    radius: int = 1,
    include_center: bool = True,
    undirected: bool = False,
    top_k: int = 10,
    **params,
) -> dict:
    """Extract ego network around a node and register the induced subgraph."""
    g, err = get_graph(store, graph_id)
    if err:
        return err

    if params:
        return error(f"Unknown parameter(s): {', '.join(sorted(params))}.")

    if node is None:
        return error("Parameter 'node' is required. Use lookup_node to find node ids.")

    err = check_node(g, node, "node")
    if err:
        return err

    if isinstance(radius, bool) or not isinstance(radius, int) or not (1 <= radius <= 10):
        return error(f"radius must be an integer between 1 and 10; got {radius!r}.")

    if not isinstance(include_center, bool):
        return error(f"include_center must be a boolean; got {include_center!r}.")

    if not isinstance(undirected, bool):
        return error(f"undirected must be a boolean; got {undirected!r}.")

    k, err = check_top_k(top_k)
    if err:
        return err

    # BFS from focal node up to radius hops
    dist = {node: 0}
    queue = deque([node])
    while queue:
        u = queue.popleft()
        d = dist[u]
        if d < radius:
            if g.directed and not undirected:
                nbrs = g.out_neighbors(u)
            else:
                nbrs = g.undirected_neighbors(u)
            for v in nbrs:
                if v not in dist:
                    dist[v] = d + 1
                    queue.append(v)

    # Determine nodes in induced subgraph
    keep_set = set(dist.keys())
    if not include_center:
        keep_set.discard(node)

    # Preserve deterministic ordering from parent graph
    ego_nodes = [n for n in g.nodes() if n in keep_set]

    # Register induced subgraph in store
    desc = f"Ego network around '{node}' (radius={radius}) in '{graph_id}'"
    sub_id = store.subgraph(graph_id, ego_nodes, desc)
    sub = store.get(sub_id)

    # Format result preview sorted by (distance, node_id)
    sorted_nodes = sorted(ego_nodes, key=lambda n: (dist[n], n))
    preview_nodes = sorted_nodes[:k]
    nodes_list = []
    for n in preview_nodes:
        if not sub.directed:
            deg = len(sub.undirected_neighbors(n)) + (1 if sub.has_edge(n, n) else 0)
        else:
            deg = len(sub.out_neighbors(n)) + len(sub.in_neighbors(n))
        nodes_list.append(node_ref(g, n, distance=int(dist[n]), degree_in_ego=deg))

    result = {
        "center": node_ref(g, node),
        "radius": int(radius),
        "include_center": bool(include_center),
        "undirected": bool(undirected),
        "node_count": sub.number_of_nodes(),
        "edge_count": sub.number_of_edges(),
        "nodes": nodes_list,
    }

    summary = (
        f"Ego network of '{g.label(node)}' ({node}) with radius {radius} in '{graph_id}' "
        f"contains {sub.number_of_nodes()} nodes and {sub.number_of_edges()} edges "
        f"(registered as '{sub_id}')."
    )

    out = ok(result, summary, result_graph_id=sub_id)

    # Safeguard against output size exceeding MAX_OUTPUT_BYTES (8 KB)
    while nodes_list and len(json.dumps(out, allow_nan=False).encode("utf-8")) > MAX_OUTPUT_BYTES:
        nodes_list.pop()
        out["result"]["nodes"] = nodes_list

    return out
