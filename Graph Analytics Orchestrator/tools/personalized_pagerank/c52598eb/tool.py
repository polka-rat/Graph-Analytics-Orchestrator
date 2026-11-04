"""Personalized PageRank: how relevant every node is to one seed node.

A random walker follows an out-edge with probability alpha (chosen in proportion to edge
weight) and jumps back to the seed with probability 1 - alpha. A walker stuck at a node
with no out-edges also jumps back to the seed. The stationary distribution is found by
power iteration, which matches networkx.pagerank(G, personalization={seed: 1}, alpha=alpha).
Each iteration is O(n + m); it usually converges in well under 200 iterations.
"""
import json

from graphkit.contract import MAX_OUTPUT_BYTES, check_node, check_top_k, error, get_graph, node_ref, ok

MAX_ITER = 1000
TOL = 1e-12  # L1 change between iterations


def _fits(out):
    """True if the response stays under the contract's 8 KB limit."""
    return len(json.dumps(out, sort_keys=True).encode("utf-8")) <= MAX_OUTPUT_BYTES


def run(store, graph_id, node=None, top_k=10, alpha=0.85, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     f"personalized_pagerank takes graph_id, node, top_k and alpha.")
    if node is None:
        return error("Missing parameter 'node': the seed node id. Use lookup_node to find it from a name.")
    err = check_node(g, node)
    if err:
        return err
    k, err = check_top_k(top_k)
    if err:
        return err
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float)) or not 0.0 < alpha < 1.0:
        return error(f"alpha (the probability of following an edge) must be a number strictly between "
                     f"0 and 1, such as 0.85; got {alpha!r}.")

    nodes = g.nodes()
    n = len(nodes)
    index = {u: i for i, u in enumerate(nodes)}
    seed = index[node]

    # Transition lists, computed once: for each node, [(target index, probability), ...].
    # Weighted graphs split the walk in proportion to edge weight (as NetworkX does).
    trans = []
    dangling = []
    for i, u in enumerate(nodes):
        nbrs = g.out_neighbors(u)
        total = float(sum(nbrs.values()))
        if not nbrs or total <= 0.0:
            trans.append(())
            dangling.append(i)
        else:
            trans.append(tuple((index[v], w / total) for v, w in nbrs.items()))

    rank = [0.0] * n
    rank[seed] = 1.0  # start at the seed; the fixed point does not depend on the start
    iterations = 0
    for iterations in range(1, MAX_ITER + 1):
        new = [0.0] * n
        for i, edges in enumerate(trans):
            r = rank[i]
            if r and edges:
                ar = alpha * r
                for j, p in edges:
                    new[j] += ar * p
        # Teleport (1 - alpha) plus all the mass stuck at dead ends goes back to the seed.
        stuck = sum(rank[i] for i in dangling)
        new[seed] += (1.0 - alpha) + alpha * stuck
        change = sum(abs(a - b) for a, b in zip(new, rank))
        rank = new
        if change < TOL:
            break

    scores = {u: rank[i] for i, u in enumerate(nodes)}
    # Highest score first; ties broken by node id (ascending).
    order = sorted(nodes, key=lambda u: (-round(scores[u], 6), u))
    ranked = order[:k]

    top = next((u for u in order if u != node and scores[u] > 0.0), None)
    if top is not None:
        summary = (f"Most relevant to {g.label(node)} ({node}) is {g.label(top)} ({top}), with personalized "
                   f"PageRank {round(scores[top], 6)}; the seed itself scores {round(scores[node], 6)}.")
    else:
        summary = (f"No other node can be reached from {g.label(node)} ({node}), so all of the "
                   f"personalized PageRank (1.0) stays on the seed.")

    out = ok([node_ref(g, u, score=round(scores[u], 6)) for u in ranked], summary)
    shown = len(ranked)
    while shown > 1 and not _fits(out):  # keep the response under 8 KB
        shown -= 1
        out = ok([node_ref(g, u, score=round(scores[u], 6)) for u in ranked[:shown]],
                 summary + f" Showing the top {shown} of {len(ranked)} requested to stay under 8 KB.")
    return out
