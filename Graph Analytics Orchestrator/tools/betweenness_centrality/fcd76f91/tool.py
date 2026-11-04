"""betweenness_centrality: which nodes sit on the most shortest paths between others.

Uses Brandes' algorithm. For each source node:
  1. find shortest paths from it (BFS, or Dijkstra if weighted) and count how many
     shortest paths reach each node (sigma) and from which nodes (preds),
  2. walk back from the farthest node and pass "dependency" back to the predecessors.
Adding up the dependencies over all sources gives the betweenness of every node.
I scale the scores the same way NetworkX does, so results can be compared with it.
"""
import json
from collections import deque
from heapq import heappop, heappush

from graphkit.contract import MAX_OUTPUT_BYTES, check_node, check_top_k, error, get_graph, node_ref, ok

SIZE_BUDGET = MAX_OUTPUT_BYTES - 1024  # keep some space for the summary


def make_adjacency(g, weighted):
    """Turn the graph into lists indexed by number, which is much faster to loop over than dicts."""
    nodes = sorted(g.nodes())
    pos = {n: i for i, n in enumerate(nodes)}
    adj = []
    for n in nodes:
        adj.append([(pos[v], w if weighted else 1.0) for v, w in sorted(g.out_neighbors(n).items())])
    return nodes, adj


def shortest_paths_bfs(adj, s):
    """Unweighted shortest paths from s. Returns (visit order, predecessors, path counts)."""
    n = len(adj)
    dist = [-1] * n
    sigma = [0] * n
    preds = [[] for _ in range(n)]
    dist[s] = 0
    sigma[s] = 1
    order = []
    queue = deque([s])
    while queue:
        v = queue.popleft()
        order.append(v)
        for w, _ in adj[v]:
            if dist[w] < 0:
                dist[w] = dist[v] + 1
                queue.append(w)
            if dist[w] == dist[v] + 1:
                sigma[w] += sigma[v]
                preds[w].append(v)
    return order, preds, sigma


def shortest_paths_dijkstra(adj, s):
    """Same as shortest_paths_bfs, but edge weights are distances."""
    n = len(adj)
    sigma = [0] * n
    preds = [[] for _ in range(n)]
    best = {s: 0.0}
    done = [False] * n
    order = []
    sigma[s] = 1
    heap = [(0.0, s, s)]  # (distance, node, the node we came from)
    while heap:
        d, v, came_from = heappop(heap)
        if done[v]:
            continue
        if v != s:
            sigma[v] += sigma[came_from]
        done[v] = True
        order.append(v)
        for w, weight in adj[v]:
            new_d = d + weight
            if not done[w] and (w not in best or new_d < best[w]):
                # found a shorter way to w, forget the old ones
                best[w] = new_d
                heappush(heap, (new_d, w, v))
                sigma[w] = 0
                preds[w] = [v]
            elif new_d == best[w]:
                # another path of the same length
                sigma[w] += sigma[v]
                preds[w].append(v)
    return order, preds, sigma


def brandes(adj, directed, weighted, normalized):
    n = len(adj)
    find_paths = shortest_paths_dijkstra if weighted else shortest_paths_bfs
    bc = [0.0] * n

    for s in range(n):
        order, preds, sigma = find_paths(adj, s)
        delta = [0.0] * n
        for w in reversed(order):  # farthest nodes first
            share = (1.0 + delta[w]) / sigma[w]
            for v in preds[w]:
                delta[v] += sigma[v] * share
            if w != s:
                bc[w] += delta[w]

    # Undirected graphs count every pair twice (once from each end), hence the 0.5.
    if normalized:
        scale = 1.0 / ((n - 1) * (n - 2)) if n > 2 else None
    else:
        scale = None if directed else 0.5
    if scale is not None:
        bc = [b * scale for b in bc]
    return bc


def run(store, graph_id, top_k=10, node=None, weighted=False, normalized=True, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     f"betweenness_centrality takes graph_id, top_k, node, weighted and normalized.")
    k, err = check_top_k(top_k)
    if err:
        return err
    for name, value in (("weighted", weighted), ("normalized", normalized)):
        if not isinstance(value, bool):
            return error(f"{name} must be true or false; got {value!r}.")
    if node is not None:
        err = check_node(g, node)
        if err:
            return err
    if g.number_of_nodes() == 0:
        return error(f"Graph '{graph_id}' has no nodes. Use list_graphs to pick another graph.")
    if not g.weighted:
        weighted = False  # all weights are 1, so BFS gives the same answer and is faster
    if weighted and any(w < 0 for _, _, w in g.edges()):
        return error(f"Graph '{graph_id}' has negative edge weights, so weighted shortest paths are undefined. "
                     f"Call again with weighted=false.")

    nodes, adj = make_adjacency(g, weighted)
    scores = brandes(adj, g.directed, weighted, normalized)

    # Sort on the rounded score so tiny float differences don't change the order; ties go by node id.
    ranked = sorted(((round(s, 6), n) for n, s in zip(nodes, scores)), key=lambda t: (-t[0], t[1]))
    result = [node_ref(g, n, score=s, rank=i) for i, (s, n) in enumerate(ranked[:k], 1)]

    paths = "weighted (edge weights as distances)" if weighted else "unweighted (hop count)"
    best = result[0]
    if best["score"] == 0:
        summary = (f"No node of '{graph_id}' lies on a shortest path between two other nodes: every "
                   f"betweenness score is 0 ({paths} shortest paths).")
    else:
        summary = (f"{best['label']} ({best['id']}) has the highest betweenness centrality ({best['score']}) of "
                   f"{len(nodes)} nodes in '{graph_id}', so it is the main broker on {paths} shortest paths.")

    # Airport names are long, so 100 of them can go over 8 KB. Drop from the bottom until it fits.
    while len(result) > 1 and len(json.dumps(result).encode("utf-8")) > SIZE_BUDGET:
        result.pop()
    if len(result) < min(k, len(nodes)):
        summary += f" Only the top {len(result)} nodes are listed to keep the output small."

    if node is not None:
        rank = next(i for i, (_, n) in enumerate(ranked, 1) if n == node)
        score = ranked[rank - 1][0]
        if rank > len(result):
            result.append(node_ref(g, node, score=score, rank=rank))
        summary += f" {g.label(node)} ({node}) ranks {rank} of {len(nodes)} with score {score}."
    return ok(result, summary)
