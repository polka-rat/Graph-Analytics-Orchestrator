"""Closeness centrality: how close each node is to all the others, by shortest-path distance.

For a node u that reaches r other nodes at total distance D, closeness is (r / D) * (r / (n - 1)):
the inverse of the average distance, scaled by the share of the graph it reaches (the
Wasserman–Faust correction, so nodes in small components do not look central). Distances are
hop counts by breadth-first search, or edge weights by Dijkstra's algorithm. On directed graphs
the default measures distance *to* u from the other nodes ("incoming"), as NetworkX does.
"""
import heapq
import json
import math

from graphkit.contract import (DEFAULT_TOP_K, MAX_OUTPUT_BYTES, check_node, check_top_k, error, get_graph,
                               node_ref, ok)

DIRECTIONS = ("incoming", "outgoing")
OUTPUT_BUDGET = MAX_OUTPUT_BYTES - 64  # stay safely under the 8 KB limit


def _as_top_k(value):
    """Accept what LLMs send for a count: null (use the default), 5.0 or "5"."""
    if value is None:
        return DEFAULT_TOP_K
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value)
    return value


def _as_node(g, value):
    """Null or "" means no node; 5 means node '5'; case and stray spaces are ignored if one node matches."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, int) and not isinstance(value, bool):
        value = str(value)
    if isinstance(value, str) and not g.has_node(value):
        matches = [n for n in g.nodes() if n.lower() == value.strip().lower()]
        if len(matches) == 1:
            return matches[0]
    return value


def _as_bool(value, default):
    """Accept null (use the default) and "true"/"false" as text."""
    if value is None:
        return default
    if isinstance(value, str) and value.strip().lower() in ("true", "false"):
        return value.strip().lower() == "true"
    return value


def _as_direction(value):
    """Null means the default; accept any case, stray spaces, and 'in'/'out'."""
    if value is None:
        return "incoming"
    if isinstance(value, str):
        value = value.strip().lower()
        return {"in": "incoming", "out": "outgoing"}.get(value, value)
    return value


def _plural(n, word):
    return f"{n:,} {word}" + ("" if n == 1 else "s")


def _hop_distances(step, source):
    """Breadth-first search: hops from source to every node it reaches, following step(u)."""
    dist = {source: 0}
    frontier = [source]
    while frontier:
        nxt = []
        for u in frontier:
            for v in step(u):
                if v not in dist:
                    dist[v] = dist[u] + 1
                    nxt.append(v)
        frontier = nxt
    return dist


def _weighted_distances(step, source):
    """Dijkstra's algorithm: weighted distance from source to every node it reaches."""
    dist = {}
    best = {source: 0.0}
    heap = [(0.0, source)]
    while heap:
        d, u = heapq.heappop(heap)
        if u in dist:
            continue
        dist[u] = d
        for v, w in step(u).items():
            nd = d + w
            if v not in dist and (v not in best or nd < best[v]):
                best[v] = nd
                heapq.heappush(heap, (nd, v))
    return dist


def _closeness(g, direction, weighted):
    """{node: (closeness, nodes reached, total distance)} for every node."""
    # Distance *to* u from the others is distance *from* u when edges are followed backwards.
    step = g.in_neighbors if direction == "incoming" else g.out_neighbors
    shortest = _weighted_distances if weighted else _hop_distances
    n = g.number_of_nodes()
    scores = {}
    for u in g.nodes():
        dist = shortest(step, u)
        total = sum(dist.values())
        reached = len(dist) - 1
        c = 0.0
        if total > 0.0 and n > 1:
            c = reached / total
            c *= reached / (n - 1)
        scores[u] = (c, reached, total)
    return scores


def _size(out):
    return len(json.dumps(out, sort_keys=True).encode("utf-8"))


def run(store, graph_id=None, top_k=10, node=None, weighted=False, direction="incoming", **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. closeness_centrality takes graph_id, top_k, "
                     f"node, weighted and direction.")
    k, err = check_top_k(_as_top_k(top_k))
    if err:
        return err
    node = _as_node(g, node)
    if node is not None:
        err = check_node(g, node)
        if err:
            return err
    weighted = _as_bool(weighted, False)
    if not isinstance(weighted, bool):
        return error(f"weighted must be true or false; got {weighted!r}.")
    direction = _as_direction(direction)
    if direction not in DIRECTIONS:
        return error(f"direction must be 'incoming' or 'outgoing'; got {direction!r}.")
    if g.number_of_nodes() == 0:
        return error(f"Graph '{graph_id}' has no nodes. Use list_graphs to pick another graph.")
    if weighted and any(not (w >= 0 and math.isfinite(w)) for _, _, w in g.edges()):
        return error(f"Graph '{graph_id}' has negative or non-finite edge weights, so weighted distances are "
                     f"undefined. Call again with weighted=false to use hop counts.")

    scores = _closeness(g, direction, weighted)
    n = g.number_of_nodes()
    # Rank on scores rounded to 12 places, so float noise from summation order cannot break a true tie;
    # ties are then broken by node id.
    ranked = sorted(scores, key=lambda u: (-round(scores[u][0], 12), u))
    if not g.directed:
        towards = "from the other nodes"
    elif direction == "incoming":
        towards = "from the nodes that can reach it"
    else:
        towards = "to the nodes it can reach"
    partial = sum(1 for u in ranked if scores[u][1] < n - 1)
    caveat = ""
    if partial:
        if not g.directed:
            caveat = f" The graph is disconnected: {partial} of {n} nodes cannot reach every other node"
        elif direction == "incoming":
            caveat = f" {partial} of {n} nodes cannot be reached from every other node"
        else:
            caveat = f" {partial} of {n} nodes cannot reach every other node"
        caveat += ", so their scores are scaled down by the share of nodes they reach."
    if g.directed:
        caveat += f" Direction: {direction}."

    def describe(u):
        c, reached, total = scores[u]
        if reached == 0:
            cut_off = "cannot be reached from any other node" if g.directed and direction == "incoming" \
                else "has no path to any other node"
            return f"{g.label(u)} ({u}) {cut_off}, so its closeness is 0"
        if total == 0:
            return (f"{g.label(u)} ({u}) is at distance 0 from {_plural(reached, 'other node')} (zero-weight "
                    f"edges), so its closeness is undefined and reported as 0")
        avg = round(total / reached, 3)
        distance = f"an average weighted distance of {avg}" if weighted else f"on average {avg} hops"
        return (f"{g.label(u)} ({u}) has closeness {round(c, 6)}, {distance} {towards} "
                f"({reached} of {_plural(n - 1, 'other node')})")

    if node is not None:
        c, reached, total = scores[node]
        avg = round(total / reached, 6) if reached else None
        result = node_ref(g, node, score=round(c, 6), rank=ranked.index(node) + 1, avg_distance=avg, reached=reached)
        summary = f"{describe(node)}; it ranks {result['rank']} of {n} in '{graph_id}'.{caveat}"
        return ok(result, summary)

    if scores[ranked[0]][0] == 0.0:
        result = [node_ref(g, u, score=0.0) for u in ranked[:k]]
        if any(reached for _, reached, _ in scores.values()):
            return ok(result, f"Every shortest-path distance in '{graph_id}' is 0 (zero-weight edges), so closeness "
                              f"is undefined and reported as 0 for every node. Use weighted=false to count hops.")
        return ok(result, f"No node in '{graph_id}' can reach another, so every closeness score is 0.")

    result = [node_ref(g, u, score=round(scores[u][0], 6)) for u in ranked[:k]]
    summary = f"{describe(ranked[0])}, the highest of {n} nodes in '{graph_id}'.{caveat}"
    out = ok(result, summary)
    while _size(out) > OUTPUT_BUDGET:  # long labels with top_k near 100: drop the lowest-ranked entries
        result.pop()
        out["summary"] = summary + f" Only the top {len(result)} nodes are listed to keep the response under 8 KB."
    return out
