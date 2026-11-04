"""Closeness centrality: how close each node is, on average, to all the other nodes.

Rules (the validator checks them):
- Implement the algorithm yourself: standard library, NumPy and graphkit only.
- Get graphs only from the store; never open files, print, or use the network.
- Never crash: return error("what went wrong and how to fix it") instead.
- Return every node as node_ref(g, node, ...), so it has both an id and a label.
- Keep the output under 8 KB: respect top_k.
- Be deterministic: same input, same output. Randomised algorithms take a `seed` parameter (default 0).
"""
import json
from collections import deque

from graphkit.contract import MAX_OUTPUT_BYTES, check_top_k, error, get_graph, node_ref, ok


def _closeness(g):
    """{node: (closeness, average distance)}, distances counted in hops (edge weights ignored).

    A breadth-first search from each node gives its distance to every node it can reach.
    closeness = (r - 1) / (sum of distances) * (r - 1) / (n - 1), where r is the number of
    nodes reached (the node itself included) and n the number of nodes. The second factor
    (Wasserman and Faust) lowers the score of nodes that reach only part of a disconnected graph.
    On a directed graph the distance is measured TO the node (along incoming edges), as in NetworkX.
    """
    nodes = g.nodes()
    n = len(nodes)
    index = {v: i for i, v in enumerate(nodes)}
    # Work with integer positions and plain lists: much faster than dicts on airports.
    step = g.in_neighbors if g.directed else g.neighbors
    adj = [[index[u] for u in step(v)] for v in nodes]

    out = {}
    for s in range(n):
        dist = [-1] * n
        dist[s] = 0
        queue = deque([s])
        total, reached = 0, 1
        while queue:
            v = queue.popleft()
            for w in adj[v]:
                if dist[w] < 0:
                    dist[w] = dist[v] + 1
                    total += dist[w]
                    reached += 1
                    queue.append(w)
        if total > 0 and n > 1:
            score = (reached - 1) / total * (reached - 1) / (n - 1)
            out[nodes[s]] = (score, total / (reached - 1))
        else:
            out[nodes[s]] = (0.0, None)  # reaches no other node
    return out


def run(store, graph_id, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. closeness_centrality takes graph_id and top_k.")
    k, err = check_top_k(top_k)
    if err:
        return err
    n = g.number_of_nodes()
    if n == 0:
        return error(f"Graph '{graph_id}' has no nodes. Use list_graphs to pick another graph.")

    scores = _closeness(g)
    # Highest closeness first; ties broken by node id so the output is deterministic.
    top = sorted(scores.items(), key=lambda item: (-round(item[1][0], 6), item[0]))[:k]
    nodes = [node_ref(g, v, closeness=round(c, 6),
                      average_distance=None if d is None else round(d, 6)) for v, (c, d) in top]
    best = nodes[0]
    if best["closeness"] == 0:
        summary = f"No node of '{graph_id}' can reach another node, so every closeness centrality is 0."
    else:
        if g.directed:
            meaning = f"on average, the nodes that can reach it are {best['average_distance']} hops away"
        else:
            meaning = f"on average it is {best['average_distance']} hops from the nodes it can reach"
        summary = (f"{best['label']} ({best['id']}) has the highest closeness centrality ({best['closeness']}) "
                   f"of {n} nodes in '{graph_id}': {meaning}.")
    out = ok(nodes, summary)

    # Long labels (e.g. airport names) can push top_k=100 over the 8 KB limit: return fewer nodes.
    while len(json.dumps(out, sort_keys=True).encode("utf-8")) > MAX_OUTPUT_BYTES - 200:
        nodes.pop()
        out = ok(nodes, f"{summary} Only the top {len(nodes)} nodes are listed, to keep the output under 8 KB.")
    return out
