"""Finds all nodes within k hops of a given node (breadth-first search) and registers them as a subgraph.

Rules (the validator checks them):
- Implement the algorithm yourself: standard library, NumPy and graphkit only.
- Get graphs only from the store; never open files, print, or use the network.
- Never crash: return error("what went wrong and how to fix it") instead.
- Return every node as node_ref(g, node, ...), so it has both an id and a label.
- Keep the output under 8 KB: respect top_k.
- Be deterministic: same input, same output. Randomised algorithms take a `seed` parameter (default 0).
"""
from graphkit.contract import MAX_OUTPUT_BYTES, check_node, check_top_k, error, get_graph, node_ref, ok
from collections import deque
import json


def run(store, graph_id, node=None, k=1, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    err = check_node(g, node)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}.")
    top_k, err = check_top_k(top_k)
    if err:
        return err

    if isinstance(k, bool) or not isinstance(k, int) or k < 1:
        return error(f"k must be a whole number of at least 1 (the number of hops); got {k!r}.")

    # BFS from node
    dist = {node: 0}
    q = deque([node])
    while q:
        curr_node = q.popleft()
        if dist[curr_node] == k:
            continue
        for i in g.out_neighbors(curr_node):
            if i not in dist:
                dist[i] = dist[curr_node] + 1
                q.append(i)

    # Sorting the pairs orders them by distance first, then by node id.
    pairs = []
    for n in dist:
        if n != node:
            pairs.append((dist[n], n))
    pairs.sort()

    # register the subgraph of the start node and every node within k hops.
    source_name = f"{g.label(node)} ({node})"
    sub_nodes = sorted(dist)
    sub_id = store.subgraph(graph_id, sub_nodes, f"Nodes within {k} hop(s) of {source_name} in '{graph_id}'")

    nodes = []
    for d, n in pairs[:top_k]:
        nodes.append(node_ref(g, n, distance=d))

    result = {
        "source": node_ref(g, node),
        "k": k,
        "count": len(pairs),
        "nodes": nodes,
    }

    hops = f"{k} hop(s)"
    if g.directed:
        hops = hops + " following outgoing edges"

    # Long labels can push 100 nodes past the 8 KB limit, so drop the farthest, listed nodes until the whole output fits.
    while True:
        if len(pairs) == 0:
            summary = f"No other node is within {hops} of {source_name}."
        elif len(nodes) == len(pairs):
            summary = f"{len(pairs)} nodes are within {hops} of {source_name}; all are listed with their distances."
        else:
            summary = (f"{len(pairs)} nodes are within {hops} of {source_name}; the nearest {len(nodes)} are "
                       f"listed with their distances, and the full set is in result_graph_id.")
        out = ok(result, summary, result_graph_id=sub_id)
        if len(json.dumps(out).encode("utf-8")) <= MAX_OUTPUT_BYTES or len(nodes) == 0:
            return out
        nodes.pop()
