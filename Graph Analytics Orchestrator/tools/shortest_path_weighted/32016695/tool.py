"""shortest_path_weighted: the lowest-total-weight path between two nodes, by Dijkstra's algorithm.

Edge weights are costs (for airports, kilometres). Returns the total distance and the path,
with the weight of each step and the running total at each node.
"""
import heapq
import json

from graphkit.contract import MAX_OUTPUT_BYTES, error, get_graph, node_ref, ok

RESULT_BUDGET = MAX_OUTPUT_BYTES - 1500
TRUE_WORDS, FALSE_WORDS = ("true", "yes", "1"), ("false", "no", "0")


# ----- input handling: LLMs send "true" or "maa"; accept what is unambiguous, explain what is not
def _resolve_node(g, value, param):
    """(node id, None) for an id of g, matched exactly or ignoring case, else (None, error)."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None, error(f"Parameter '{param}' is missing: give the id of a node in '{g.graph_id}'. "
                           f"Use lookup_node to find node ids from names.")
    if not isinstance(value, str):
        return None, error(f"Parameter '{param}' must be a node id (a string); got {value!r}. "
                           f"Use lookup_node to find node ids.")
    value = value.strip()
    if g.has_node(value):
        return value, None
    same = [n for n in g.nodes() if n.lower() == value.lower()]
    if len(same) == 1:
        return same[0], None
    return None, error(f"Node '{value}' (parameter '{param}') is not in graph '{g.graph_id}'. "
                       f"Use lookup_node to find node ids.")


def _boolean(value, name):
    """(bool, None) for true/false, also as the words "true"/"false" or 1/0, else (None, error)."""
    if isinstance(value, bool):
        return value, None
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value), None
    if isinstance(value, str) and value.strip().lower() in TRUE_WORDS + FALSE_WORDS:
        return value.strip().lower() in TRUE_WORDS, None
    return None, error(f"{name} must be true or false; got {value!r}.")


# ----- the algorithm
def _neighbours(g, node, ignore_direction):
    return g.undirected_neighbors(node) if ignore_direction else g.out_neighbors(node)


def _dijkstra(g, source, target, ignore_direction):
    """Returns (distance, predecessor map); distance is None if target cannot be reached.

    Ties are deterministic: the heap pops equal distances in node-id order, and a node's
    predecessor only changes when a strictly shorter distance is found.
    """
    dist = {source: 0.0}
    prev = {}
    done = set()
    heap = [(0.0, source)]
    while heap:
        d, u = heapq.heappop(heap)
        if u in done:
            continue  # a stale entry: u was already settled with a smaller distance
        done.add(u)
        if u == target:
            return d, prev
        for v, w in _neighbours(g, u, ignore_direction).items():
            nd = d + w
            if v not in done and nd < dist.get(v, float("inf")):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, v))
    return None, prev


def _fmt(x):
    return f"{x:,.0f}" if x >= 100 else f"{x:g}"


def run(store, graph_id, source=None, target=None, ignore_direction=False, top_k=None, **params):
    # top_k is accepted and ignored: orchestrators pass it to every tool, and a path has no top-k.
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     f"shortest_path_weighted takes graph_id, source, target and ignore_direction.")
    source, err = _resolve_node(g, source, "source")
    if err:
        return err
    target, err = _resolve_node(g, target, "target")
    if err:
        return err
    ignore_direction, err = _boolean(ignore_direction, "ignore_direction")
    if err:
        return err
    negative = next(((u, v, w) for u, v, w in g.edges() if w < 0), None)
    if negative:
        u, v, w = negative
        return error(f"Edge {u}->{v} has negative weight {w}; Dijkstra's algorithm needs weights of zero "
                     f"or more, so it cannot be used on '{graph_id}'.")
    ignore_direction = ignore_direction and g.directed  # no-op on undirected graphs

    distance, prev = _dijkstra(g, source, target, ignore_direction)
    src_name, tgt_name = f"{g.label(source)} ({source})", f"{g.label(target)} ({target})"
    unit = "" if g.weighted else " (the graph is unweighted, so every edge counts 1 and this is the hop count)"

    if distance is None:
        result = {"source": node_ref(g, source), "target": node_ref(g, target), "reachable": False,
                  "distance": None, "hops": None, "path": []}
        how = "even ignoring edge direction" if ignore_direction else (
            "following edge directions; try ignore_direction=true" if g.directed else "")
        return ok(result, f"There is no path from {src_name} to {tgt_name} in '{graph_id}'"
                          f"{' (' + how + ')' if how else ''}.")

    nodes = [target]
    while nodes[-1] != source:
        nodes.append(prev[nodes[-1]])
    nodes.reverse()

    path, total = [node_ref(g, source, step_weight=None, distance_so_far=0.0)], 0.0
    for u, v in zip(nodes, nodes[1:]):
        w = _neighbours(g, u, ignore_direction)[v]  # the same weight Dijkstra used
        total += w
        path.append(node_ref(g, v, step_weight=round(w, 6), distance_so_far=round(total, 6)))

    result = {"source": node_ref(g, source), "target": node_ref(g, target), "reachable": True,
              "distance": round(distance, 6), "hops": len(nodes) - 1, "path": path, "path_truncated": False}
    # Very long paths: keep both ends and drop the middle until the output fits in 8 KB.
    while len(json.dumps(result).encode("utf-8")) > RESULT_BUDGET and len(path) > 4:
        del path[len(path) // 2]
        result["path_truncated"] = True

    route = " -> ".join(p["id"] for p in path) if not result["path_truncated"] else \
        f"{path[0]['id']} -> ... -> {path[-1]['id']}"
    if source == target:
        return ok(result, f"{src_name} is both the source and the target, so the distance is 0.")
    return ok(result, f"The shortest path from {src_name} to {tgt_name} has total weight {_fmt(distance)}"
                      f"{unit} over {len(nodes) - 1} edge(s): {route}.")
