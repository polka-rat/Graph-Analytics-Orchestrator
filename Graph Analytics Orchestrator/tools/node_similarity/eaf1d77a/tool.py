"""node_similarity: common neighbours and Jaccard similarity of nodes.

Two modes:
  * Pair mode (node_a and node_b given): the common neighbours of the two nodes
    and their Jaccard score |N(a) & N(b)| / |N(a) | N(b)|.
  * Ranking mode (only node_a given): the top_k nodes most similar to node_a,
    ranked by Jaccard score (ties broken by node id, ascending).

Definitions follow NetworkX: the Jaccard score uses the full neighbour sets
(nx.jaccard_coefficient), and the reported common neighbours exclude the two
nodes themselves (nx.common_neighbors).

Only the graph store, the standard library and graphkit are used.
"""
import json

from graphkit.contract import error, node_ref, ok

DEFAULT_TOP_K = 10
MAX_TOP_K = 100
MAX_BYTES = 7500          # stay safely under the 8 KB response limit
DIRECTIONS = ("any", "out", "in")


# ----------------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------------
def _sort_key(node):
    """Ascending node-id order that also works if ids are numbers."""
    return (isinstance(node, str), node)


def _resolve(node, node_set):
    """Match a node id given by the user/LLM (always text) to a real node id."""
    if node in node_set:
        return node
    text = str(node).strip()
    if text in node_set:
        return text
    try:
        number = int(text)
    except ValueError:
        return None
    return number if number in node_set else None


def _parse_top_k(top_k):
    if isinstance(top_k, bool):
        raise ValueError
    top_k = int(top_k)
    if top_k < 1:
        raise ValueError
    return min(top_k, MAX_TOP_K)


def _neighbour_set(g, node, direction):
    """Neighbours of node: 'out' follows edges forward, 'in' backward, 'any' both."""
    if direction == "out":
        return set(g.out_neighbors(node))
    if direction == "in":
        return set(g.in_neighbors(node))
    return set(g.undirected_neighbors(node))


def _reverse_neighbour_set(g, node, direction):
    """Nodes b that have `node` in their neighbour set for this direction."""
    if direction == "out":
        return set(g.in_neighbors(node))
    if direction == "in":
        return set(g.out_neighbors(node))
    return set(g.undirected_neighbors(node))


def _jaccard(n_a, n_b):
    union = len(n_a | n_b)
    return 0.0 if union == 0 else len(n_a & n_b) / union


def _fit(items, build):
    """Drop trailing list items until the response fits under MAX_BYTES."""
    response = build(items)
    while items and len(json.dumps(response, default=str)) > MAX_BYTES:
        items = items[:-1]
        response = build(items)
    return response


# ----------------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------------
def run(store, graph_id: str, **params) -> dict:
    try:
        return _run(store, graph_id, **params)
    except Exception as exc:  # never crash: report the problem instead
        return error(f"node_similarity failed unexpectedly: {exc}")


def _run(store, graph_id, node_a=None, node_b=None, direction="any",
         top_k=DEFAULT_TOP_K, **_ignored):
    try:
        g = store.get(graph_id)
    except Exception:
        return error(f"Graph '{graph_id}' not found. Use list_graphs to see the available graph ids.")

    if node_a is None or str(node_a).strip() == "":
        return error("node_a is required. Use lookup_node to find a node id from its name.")
    direction = str(direction).lower()
    if direction not in DIRECTIONS:
        return error(f"direction must be one of {list(DIRECTIONS)}; got '{direction}'.")
    if not g.directed:
        direction = "any"          # in/out are the same on an undirected graph
    try:
        top_k = _parse_top_k(top_k)
    except (TypeError, ValueError):
        return error(f"top_k must be a positive integer (at most {MAX_TOP_K}); got {top_k!r}.")

    node_set = set(g.nodes())
    a = _resolve(node_a, node_set)
    if a is None:
        return error(f"Node '{node_a}' not found in graph '{graph_id}'. Use lookup_node to find node ids.")

    n_a = _neighbour_set(g, a, direction)
    dir_text = "" if direction == "any" else f" ({direction}-neighbours)"

    # ---------------- Pair mode ----------------
    if node_b is not None and str(node_b).strip() != "":
        b = _resolve(node_b, node_set)
        if b is None:
            return error(f"Node '{node_b}' not found in graph '{graph_id}'. Use lookup_node to find node ids.")
        if a == b:
            return error("node_a and node_b are the same node; give two different nodes.")
        n_b = _neighbour_set(g, b, direction)
        common = sorted((n_a & n_b) - {a, b}, key=_sort_key)
        score = round(_jaccard(n_a, n_b), 6)
        la, lb = g.label(a), g.label(b)

        def build(shown):
            result = {
                "node_a": node_ref(g, a),
                "node_b": node_ref(g, b),
                "direction": direction,
                "degree_a": len(n_a),
                "degree_b": len(n_b),
                "common_neighbors": len(common),
                "jaccard": score,
                "common_neighbor_nodes": [node_ref(g, w) for w in shown],
            }
            summary = (f"{la} and {lb} share {len(common)} common neighbour(s){dir_text}; "
                       f"Jaccard similarity is {score} "
                       f"({len(n_a)} and {len(n_b)} neighbours respectively).")
            if len(shown) < len(common):
                summary += f" Only the first {len(shown)} common neighbours are listed."
            return ok(result=result, summary=summary)

        return _fit(common[:MAX_TOP_K], build)

    # ---------------- Ranking mode ----------------
    # Only nodes that share at least one neighbour with `a` have a non-zero
    # score, so collect them through the neighbours of a.
    shared = {}
    for w in n_a:
        for b in _reverse_neighbour_set(g, w, direction):
            if b != a:
                shared[b] = shared.get(b, 0) + 1

    scored = []
    for b, cn in shared.items():
        n_b = _neighbour_set(g, b, direction)
        union = len(n_a) + len(n_b) - cn          # |N(a) | N(b)|
        jac = round(cn / union, 6) if union else 0.0
        common_excl = cn - (a in n_b and a in n_a) - (b in n_a and b in n_b)
        scored.append((jac, b, common_excl))
    scored.sort(key=lambda t: (-t[0], _sort_key(t[1])))
    top = scored[:top_k]
    la = g.label(a)

    def build(shown):
        result = [node_ref(g, b) | {"jaccard": jac, "common_neighbors": cn} for jac, b, cn in shown]
        if not shown:
            summary = f"{la} shares no neighbours{dir_text} with any other node, so every similarity is 0."
        else:
            best = shown[0]
            summary = (f"The node most similar to {la}{dir_text} is {g.label(best[1])} "
                       f"(Jaccard {best[0]}, {best[2]} common neighbours). "
                       f"Showing {len(shown)} of {len(scored)} nodes with non-zero similarity.")
        return ok(result=result, summary=summary)

    return _fit(top, build)
