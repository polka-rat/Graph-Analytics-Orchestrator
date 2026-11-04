"""motif_count: counts of small subgraph patterns (motifs).

Undirected graphs (and the undirected view of a directed graph):
  triangle   three nodes all linked to each other
  wedge      a path of length 2 (u - v - w), open or closed
  open_wedge a wedge whose ends are not linked (a "missing triangle")
  star3      a node with three of its neighbours (3-star)
  cycle4     a 4-cycle a - b - c - d - a (chords allowed, as in "squares")
plus the transitivity 3 * triangles / wedges and the nodes in most triangles.

Directed graphs additionally get the full triad census (the 16 types of
Holland & Leinhardt, the same names as nx.triadic_census), and the two
classic 3-node directed motifs read off it:
  feed_forward_loop  type 030T: a -> b, b -> c, a -> c
  cycle3             type 030C: a -> b -> c -> a

Algorithms:
  * Triangles: nodes are put in ascending id order; for every edge (u, v) with
    u < v, each common neighbour w > v closes one triangle, so every triangle
    is found exactly once. Cost O(sum over edges of min degree).
  * 4-cycles: for every pair (u, x) the number of 2-paths u - w - x is c(u, x);
    a 4-cycle has two diagonals, so the count is (1/2) * sum C(c(u, x), 2).
  * Triad census: Batagelj & Mrvar (2001), O(m * max degree), which only
    visits connected triads and gets the empty type 003 by subtraction.
"""
import json
from itertools import permutations

from graphkit.contract import error, node_ref, ok

DEFAULT_TOP_K = 10
MAX_TOP_K = 100
MAX_BYTES = 7500

TRIAD_NAMES = ("003", "012", "102", "021D", "021U", "021C", "111D", "111U",
               "030T", "030C", "201", "120D", "120U", "120C", "210", "300")


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def _sort_key(node):
    return (isinstance(node, str), node)


def _resolve(node, node_set):
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


def _comb2(x):
    return x * (x - 1) // 2


def _comb3(x):
    return x * (x - 1) * (x - 2) // 6


# ----------------------------------------------------------------------------
# Triad type of a 3-node directed graph (used to build a lookup table)
# ----------------------------------------------------------------------------
def _classify_triad(arcs):
    """Holland-Leinhardt name of the triad on nodes {0, 1, 2} with these arcs."""
    mutual = asym = 0
    asym_arcs = []
    for a, b in ((0, 1), (0, 2), (1, 2)):
        ab, ba = (a, b) in arcs, (b, a) in arcs
        if ab and ba:
            mutual += 1
        elif ab or ba:
            asym += 1
            asym_arcs.append((a, b) if ab else (b, a))
    outdeg = [sum(1 for s, _ in asym_arcs if s == x) for x in range(3)]
    indeg = [sum(1 for _, t in asym_arcs if t == x) for x in range(3)]

    if (mutual, asym) == (0, 0):
        return "003"
    if (mutual, asym) == (0, 1):
        return "012"
    if (mutual, asym) == (1, 0):
        return "102"
    if (mutual, asym) == (0, 2):
        if 2 in outdeg:
            return "021D"          # a <- b -> c   (out-star)
        if 2 in indeg:
            return "021U"          # a -> b <- c   (in-star)
        return "021C"              # a -> b -> c   (chain)
    if (mutual, asym) == (1, 1):
        # 111D: a <-> b <- c  (third node points INTO the mutual pair)
        # 111U: a <-> b -> c  (mutual pair points OUT to the third node)
        source, _ = asym_arcs[0]
        # the third node is the one that is not part of the mutual pair
        third = next(x for x in range(3)
                     if not any((x, y) in arcs and (y, x) in arcs for y in range(3) if y != x))
        return "111D" if source == third else "111U"
    if (mutual, asym) == (0, 3):
        return "030T" if 2 in outdeg else "030C"
    if (mutual, asym) == (2, 0):
        return "201"
    if (mutual, asym) == (1, 2):
        # the node outside the mutual pair has both asymmetric arcs
        if 2 in outdeg:
            return "120D"          # a <- b -> c, a <-> c
        if 2 in indeg:
            return "120U"          # a -> b <- c, a <-> c
        return "120C"              # a -> b -> c, a <-> c
    if (mutual, asym) == (2, 1):
        return "210"
    return "300"


# code bits: (v,u)=1 (u,v)=2 (v,w)=4 (w,v)=8 (u,w)=16 (w,u)=32, with v,u,w = 0,1,2
_BITS = (((0, 1), 1), ((1, 0), 2), ((0, 2), 4), ((2, 0), 8), ((1, 2), 16), ((2, 1), 32))
TRICODE_TO_NAME = tuple(
    _classify_triad({arc for arc, bit in _BITS if code & bit}) for code in range(64)
)


def _triad_census(nodes, succ, pred):
    """Batagelj-Mrvar triad census of a directed graph."""
    n = len(nodes)
    order = {v: i for i, v in enumerate(nodes)}
    nbr = {v: (succ[v] | pred[v]) for v in nodes}
    census = dict.fromkeys(TRIAD_NAMES, 0)

    def tricode(v, u, w):
        code = 0
        if u in succ[v]: code |= 1
        if v in succ[u]: code |= 2
        if w in succ[v]: code |= 4
        if v in succ[w]: code |= 8
        if w in succ[u]: code |= 16
        if u in succ[w]: code |= 32
        return code

    for v in nodes:
        ov = order[v]
        for u in nbr[v]:
            ou = order[u]
            if ou <= ov:
                continue
            s = (nbr[v] | nbr[u]) - {u, v}
            # triads {v, u, x} where x touches neither v nor u
            if u in succ[v] and v in succ[u]:
                census["102"] += n - len(s) - 2
            else:
                census["012"] += n - len(s) - 2
            for w in s:
                ow = order[w]
                if ou < ow or (ov < ow < ou and v not in nbr[w]):
                    census[TRICODE_TO_NAME[tricode(v, u, w)]] += 1

    total = n * (n - 1) * (n - 2) // 6
    census["003"] = total - sum(c for name, c in census.items() if name != "003")
    return census


# ----------------------------------------------------------------------------
# Undirected motifs
# ----------------------------------------------------------------------------
def _undirected_motifs(nodes, nbrs):
    order = {v: i for i, v in enumerate(nodes)}
    tri_per_node = dict.fromkeys(nodes, 0)
    triangles = 0
    for u in nodes:
        ou = order[u]
        for v in nbrs[u]:
            if order[v] <= ou:
                continue
            small, large = (nbrs[u], nbrs[v]) if len(nbrs[u]) < len(nbrs[v]) else (nbrs[v], nbrs[u])
            ov = order[v]
            for w in small:
                if order[w] > ov and w in large:
                    triangles += 1
                    tri_per_node[u] += 1
                    tri_per_node[v] += 1
                    tri_per_node[w] += 1

    wedges = sum(_comb2(len(nbrs[v])) for v in nodes)
    stars = sum(_comb3(len(nbrs[v])) for v in nodes)

    cycle4_twice = 0
    for u in nodes:
        ou = order[u]
        paths = {}
        for w in nbrs[u]:
            for x in nbrs[w]:
                if order[x] > ou:
                    paths[x] = paths.get(x, 0) + 1
        cycle4_twice += sum(_comb2(c) for c in paths.values())

    return {
        "triangles": triangles,
        "wedges": wedges,
        "open_wedges": wedges - 3 * triangles,
        "star3": stars,
        "cycle4": cycle4_twice // 2,
        "transitivity": round(3 * triangles / wedges, 6) if wedges else 0.0,
        "per_node": tri_per_node,
    }


# ----------------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------------
def run(store, graph_id: str, **params) -> dict:
    try:
        return _run(store, graph_id, **params)
    except Exception as exc:
        return error(f"motif_count failed unexpectedly: {exc}")


def _run(store, graph_id, node=None, top_k=DEFAULT_TOP_K, **_ignored):
    try:
        g = store.get(graph_id)
    except Exception:
        return error(f"Graph '{graph_id}' not found. Use list_graphs to see the available graph ids.")
    try:
        top_k = _parse_top_k(top_k)
    except (TypeError, ValueError):
        return error(f"top_k must be a positive integer (at most {MAX_TOP_K}); got {top_k!r}.")

    nodes = sorted(g.nodes(), key=_sort_key)
    if not nodes:
        return error(f"Graph '{graph_id}' has no nodes, so there are no motifs to count.")
    node_set = set(nodes)
    target = None
    if node is not None and str(node).strip() != "":
        target = _resolve(node, node_set)
        if target is None:
            return error(f"Node '{node}' not found in graph '{graph_id}'. Use lookup_node to find node ids.")

    nbrs = {v: set(g.undirected_neighbors(v)) - {v} for v in nodes}
    und = _undirected_motifs(nodes, nbrs)
    view = "undirected view" if g.directed else "undirected"

    motifs = [
        {"motif": "triangle", "count": und["triangles"], "view": view,
         "description": "three nodes all linked to each other"},
        {"motif": "wedge", "count": und["wedges"], "view": view,
         "description": "path of length 2 (u - v - w)"},
        {"motif": "open_wedge", "count": und["open_wedges"], "view": view,
         "description": "wedge whose two ends are not linked"},
        {"motif": "star3", "count": und["star3"], "view": view,
         "description": "a centre node with three of its neighbours"},
        {"motif": "cycle4", "count": und["cycle4"], "view": view,
         "description": "4-cycle a - b - c - d - a"},
    ]
    census = None
    if g.directed:
        succ = {v: set(g.out_neighbors(v)) - {v} for v in nodes}
        pred = {v: set(g.in_neighbors(v)) - {v} for v in nodes}
        census = _triad_census(nodes, succ, pred)
        motifs += [
            {"motif": "feed_forward_loop", "count": census["030T"], "view": "directed",
             "description": "a -> b, b -> c and a -> c (triad 030T)"},
            {"motif": "cycle3", "count": census["030C"], "view": "directed",
             "description": "a -> b -> c -> a (triad 030C)"},
        ]

    ranked = sorted(nodes, key=lambda v: (-und["per_node"][v], _sort_key(v)))
    ranked = [v for v in ranked if und["per_node"][v] > 0][:top_k]

    def build(shown):
        result = {
            "directed": g.directed,
            "nodes": len(nodes),
            "transitivity": und["transitivity"],
            "motifs": motifs,
            "top_triangle_nodes": [node_ref(g, v) | {"triangles": und["per_node"][v]} for v in shown],
        }
        if census is not None:
            result["triad_census"] = census
        if target is not None:
            result["node"] = node_ref(g, target) | {"triangles": und["per_node"][target]}

        parts = [f"The graph has {und['triangles']} triangles, {und['open_wedges']} open wedges "
                 f"and {und['cycle4']} 4-cycles ({view}); transitivity is {und['transitivity']}."]
        if census is not None:
            parts.append(f"Directed motifs: {census['030T']} feed-forward loops and "
                         f"{census['030C']} 3-cycles.")
        if target is not None:
            parts.append(f"{g.label(target)} is in {und['per_node'][target]} triangles.")
        elif shown:
            parts.append(f"{g.label(shown[0])} is in the most triangles "
                         f"({und['per_node'][shown[0]]}).")
        return ok(result=result, summary=" ".join(parts))

    response = build(ranked)
    while ranked and len(json.dumps(response, default=str)) > MAX_BYTES:
        ranked = ranked[:-1]
        response = build(ranked)
    return response
