"""Betweenness centrality (Brandes' algorithm): how often each node lies on shortest paths between others.

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


def _betweenness(g):
    """{node: normalized betweenness}, shortest paths counted in hops (edge weights ignored).

    Brandes (2001). For each source s:
      1. Breadth-first search from s, recording for every node w its distance, sigma[w] (the number
         of shortest paths from s to w) and preds[w] (the nodes just before w on those paths).
      2. Visit the nodes from farthest to nearest and pass "dependency" back along the paths:
         delta[v] += sigma[v] / sigma[w] * (1 + delta[w]) for each predecessor v of w.
         delta[v] is the share of shortest paths from s to all other nodes that pass through v.
    Summing delta over all sources gives the betweenness. Each ordered pair (s, t) is counted once,
    so dividing by (n - 1)(n - 2) gives the normalized value, as in NetworkX.
    """
    nodes = g.nodes()
    n = len(nodes)
    index = {v: i for i, v in enumerate(nodes)}
    # Integer positions and plain lists instead of dicts: this is what makes airports fast enough.
    adj = [[index[u] for u in g.out_neighbors(v)] for v in nodes]

    bc = [0.0] * n
    for s in range(n):
        # 1. Breadth-first search from s, counting shortest paths.
        dist = [-1] * n
        sigma = [0] * n
        preds = [[] for _ in range(n)]
        dist[s], sigma[s] = 0, 1
        order = []  # nodes in the order they are reached, i.e. by increasing distance
        queue = deque([s])
        while queue:
            v = queue.popleft()
            order.append(v)
            dv, sv = dist[v] + 1, sigma[v]
            for w in adj[v]:
                if dist[w] < 0:
                    dist[w] = dv
                    queue.append(w)
                if dist[w] == dv:  # v is just before w on a shortest path
                    sigma[w] += sv
                    preds[w].append(v)

        # 2. Accumulate dependencies, farthest nodes first.
        delta = [0.0] * n
        for w in reversed(order):
            coeff = (1.0 + delta[w]) / sigma[w]
            for v in preds[w]:
                delta[v] += sigma[v] * coeff
            if w != s:
                bc[w] += delta[w]

    scale = 1.0 / ((n - 1) * (n - 2)) if n > 2 else 1.0
    return {nodes[i]: bc[i] * scale for i in range(n)}


def run(store, graph_id, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. betweenness_centrality takes graph_id and top_k.")
    k, err = check_top_k(top_k)
    if err:
        return err
    n = g.number_of_nodes()
    if n == 0:
        return error(f"Graph '{graph_id}' has no nodes. Use list_graphs to pick another graph.")

    scores = _betweenness(g)
    # Highest betweenness first; ties broken by node id so the output is deterministic.
    top = sorted(scores.items(), key=lambda item: (-round(item[1], 6), item[0]))[:k]
    nodes = [node_ref(g, v, betweenness=round(b, 6)) for v, b in top]
    best = nodes[0]
    if best["betweenness"] == 0:
        summary = (f"No node of '{graph_id}' lies in the middle of a shortest path between two other nodes, "
                   f"so every betweenness centrality is 0.")
    else:
        summary = (f"{best['label']} ({best['id']}) has the highest betweenness centrality ({best['betweenness']}) "
                   f"of {n} nodes in '{graph_id}': on average it lies on {round(100 * best['betweenness'], 1)}% of the "
                   f"shortest paths between two other nodes, so it is the main broker.")
    out = ok(nodes, summary)

    # Long labels (e.g. airport names) can push top_k=100 over the 8 KB limit: return fewer nodes.
    while len(json.dumps(out, sort_keys=True).encode("utf-8")) > MAX_OUTPUT_BYTES - 200:
        nodes.pop()
        out = ok(nodes, f"{summary} Only the top {len(nodes)} nodes are listed, to keep the output under 8 KB.")
    return out
