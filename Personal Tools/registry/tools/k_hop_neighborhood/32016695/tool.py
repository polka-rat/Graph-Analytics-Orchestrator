"""k_hop_neighborhood: all nodes within k hops of a node, found by breadth-first search.

Returns the nodes nearest first (ties broken by node id), how many sit at each hop distance,
and registers the neighbourhood (the source plus every node found) as a subgraph.
"""
import json
from collections import deque

from graphkit.contract import MAX_OUTPUT_BYTES, MAX_TOP_K, error, get_graph, node_ref, ok

MAX_K = 10
DIRECTIONS = ("out", "in", "both")
# Leave room for the summary and the other output keys inside the 8 KB limit.
RESULT_BUDGET = MAX_OUTPUT_BYTES - 1500


# ----- input handling: LLMs send "2", 2.0 or "maa"; accept what is unambiguous, explain what is not
def _whole_number(value, name, lo, hi):
    """(int, None) if value is a whole number from lo to hi (also as "5" or 5.0), else (None, error)."""
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        value = int(value.strip())
    elif isinstance(value, float) and value.is_integer():
        value = int(value)
    if isinstance(value, bool) or not isinstance(value, int) or not lo <= value <= hi:
        return None, error(f"{name} must be a whole number from {lo} to {hi}; got {value!r}.")
    return value, None


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


# ----- the algorithm
def _neighbours(g, node, direction):
    if not g.directed or direction == "out":
        return g.out_neighbors(node)
    if direction == "in":
        return g.in_neighbors(node)
    return g.undirected_neighbors(node)


def _bfs(g, source, k, direction):
    """{node: hops} for every node reachable from source in at most k hops (source has 0)."""
    hops = {source: 0}
    queue = deque([source])
    while queue:
        u = queue.popleft()
        if hops[u] == k:
            continue
        for v in _neighbours(g, u, direction):
            if v not in hops:
                hops[v] = hops[u] + 1
                queue.append(v)
    return hops


def run(store, graph_id, node=None, k=2, direction="out", top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     f"k_hop_neighborhood takes graph_id, node, k, direction and top_k.")
    node, err = _resolve_node(g, node, "node")
    if err:
        return err
    k, err = _whole_number(k, "k (the number of hops)", 1, MAX_K)
    if err:
        return err
    if isinstance(direction, str):
        direction = direction.strip().lower()
    if direction not in DIRECTIONS:
        return error(f"direction must be one of {', '.join(DIRECTIONS)}; got {direction!r}. "
                     f"'out' follows edges forwards, 'in' backwards, 'both' ignores direction.")
    top_k, err = _whole_number(top_k, "top_k", 1, MAX_TOP_K)
    if err:
        return err
    if not g.directed:
        direction = "both"  # every edge goes both ways

    hops = _bfs(g, node, k, direction)
    found = sorted((h, n) for n, h in hops.items() if n != node)
    counts = {}
    for h, _ in found:
        counts[str(h)] = counts.get(str(h), 0) + 1

    # Always register the neighbourhood, even when it is only the start node, so that
    # result_graph_id is usable by the next tool whenever status is ok.
    name = f"{g.label(node)} ({node})"
    sub_id = store.subgraph(graph_id, [node] + [n for _, n in found],
                            f"Nodes within {k} hop(s) of {name} in '{graph_id}' (direction {direction})")

    nodes = [node_ref(g, n, hops=h) for h, n in found[:top_k]]
    result = {"source": node_ref(g, node), "k": k, "direction": direction, "count": len(found),
              "count_by_hops": counts, "nodes": nodes, "truncated": len(nodes) < len(found)}
    # Long labels can push even 100 nodes past the size limit: drop the farthest until it fits.
    while nodes and len(json.dumps(result).encode("utf-8")) > RESULT_BUDGET:
        nodes.pop()
        result["truncated"] = True

    if not found:
        edge_kind = {"out": "outgoing ", "in": "incoming ", "both": ""}[direction]
        return ok(result, f"No nodes are within {k} hop(s) of {name} in '{graph_id}': it has no {edge_kind}edges. "
                          f"The neighbourhood (just this node) is registered as graph '{sub_id}'.",
                  result_graph_id=sub_id)

    where = {"out": ", following edges forwards",
             "in": ", following edges backwards (nodes that can reach it)",
             "both": ""}[direction]
    per_hop = ", ".join(f"{c} at {h} hop(s)" for h, c in counts.items())
    shown = f" Showing the nearest {len(nodes)}." if result["truncated"] else ""
    return ok(result,
              f"{len(found)} node(s) are within {k} hop(s) of {name}{where} ({per_hop}).{shown} "
              f"The neighbourhood is registered as graph '{sub_id}'.",
              result_graph_id=sub_id)
