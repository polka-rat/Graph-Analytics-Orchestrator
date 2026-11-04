"""Maximal cliques by Bron–Kerbosch with Tomita pivoting; returns the largest cliques.

A clique is a set of nodes that are all joined to each other; it is maximal when no other
node can be added. On a directed graph, edge direction is ignored (u and v are adjacent if an
edge runs either way), as NetworkX does for find_cliques(G.to_undirected()).

Each returned clique is registered with the store as a subgraph; the largest one's id is the
result_graph_id, so other tools can run on it.
"""
import json

from graphkit.contract import (DEFAULT_TOP_K, MAX_OUTPUT_BYTES, check_node, check_top_k, error, get_graph,
                               node_ref, ok)

OUTPUT_BUDGET = MAX_OUTPUT_BYTES - 64  # stay safely under the 8 KB limit
NAMES_IN_SUMMARY = 5
MAX_CLIQUES = 1_000_000  # beyond this, enumeration could take minutes: ask for a smaller graph instead
KEEP_AT_MOST = 5_000  # cliques held in memory before pruning to the best top_k


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


def _adjacency(g):
    """Undirected adjacency sets without self-loops."""
    return {n: set(g.undirected_neighbors(n)) - {n} for n in g.nodes()}


def _bron_kerbosch(adj, R, P, X):
    """Yield every maximal clique that contains all of R, some of P and none of X.

    Iterative, with an explicit stack, so a very large clique cannot exceed Python's recursion limit.
    """
    stack = [(R, P, X)]
    while stack:
        R, P, X = stack.pop()
        if not P and not X:
            yield R
            continue
        # Tomita pivot: the node of P | X with the most neighbours in P. Only nodes of P that are
        # not neighbours of the pivot need to start a branch; the others are found inside those.
        pivot = max(P | X, key=lambda u: len(P & adj[u]))
        for v in sorted(P - adj[pivot]):
            stack.append((R + [v], P & adj[v], X & adj[v]))
            P.remove(v)  # P and X belong to this frame only; children got their own copies
            X.add(v)


def _best(cliques, k):
    """The k largest cliques, ties broken by their sorted node ids."""
    return sorted(cliques, key=lambda c: (-len(c), c))[:k]


def _size(out):
    return len(json.dumps(out, sort_keys=True).encode("utf-8"))


def _plural(n, word):
    return f"{n:,} {word}" + ("" if n == 1 else "s")


def _names(g, members):
    names = [g.label(n) for n in members[:NAMES_IN_SUMMARY]]
    if len(members) > NAMES_IN_SUMMARY:
        return ", ".join(names) + f" and {len(members) - NAMES_IN_SUMMARY} more"
    return ", ".join(names[:-1]) + f" and {names[-1]}" if len(names) > 1 else names[0]


def _fit(result, summary, top_id):
    """The response, trimmed to stay under 8 KB: drop member lists from the last cliques first,
    then whole entries, then shorten the first clique's member list."""
    def build():
        notes = ""
        listed = sum(1 for entry in result if "members" in entry)
        if listed < len(result):
            notes += (f" Members are listed for the first {listed} of the {len(result)} cliques returned "
                      f"(8 KB limit); read the others through their graph_id.")
        first = result[0]
        if len(first["members"]) < first["size"]:
            notes += (f" Only {len(first['members'])} of the {first['size']} members of the largest clique are "
                      f"listed (8 KB limit); read them all through '{first['graph_id']}'.")
        return ok(result, summary + notes, result_graph_id=top_id)

    out = build()
    listed = len(result)
    while _size(out) > OUTPUT_BUDGET and listed > 1:
        listed -= 1
        del result[listed]["members"]
        out = build()
    while _size(out) > OUTPUT_BUDGET and len(result) > 1:
        result.pop()
        out = build()
    if _size(out) > OUTPUT_BUDGET:  # one clique too big to list in full: find how many members fit
        full = result[0]["members"]
        lo, hi = 1, len(full)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            result[0]["members"] = full[:mid]
            lo, hi = (mid, hi) if _size(build()) <= OUTPUT_BUDGET else (lo, mid - 1)
        result[0]["members"] = full[:lo]
        out = build()
    return out


def run(store, graph_id=None, top_k=10, node=None, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. maximal_cliques takes graph_id, top_k and node.")
    k, err = check_top_k(_as_top_k(top_k))
    if err:
        return err
    node = _as_node(g, node)
    if node is not None:
        err = check_node(g, node)
        if err:
            return err
    if g.number_of_nodes() == 0:
        return error(f"Graph '{graph_id}' has no nodes, so it has no cliques. Use list_graphs to pick another graph.")

    adj = _adjacency(g)
    start = ([], set(adj), set()) if node is None else ([node], set(adj[node]), set())
    best, count, largest, n_largest = [], 0, 0, 0
    for clique in _bron_kerbosch(adj, *start):
        count += 1
        if count > MAX_CLIQUES:
            return error(f"Graph '{graph_id}' has more than {MAX_CLIQUES:,} maximal cliques, too many to list in "
                         f"time. Run this tool on a smaller subgraph (for example from filter_nodes), or pass "
                         f"node to list only the cliques that contain one node.")
        if len(clique) > largest:
            largest, n_largest = len(clique), 1
        elif len(clique) == largest:
            n_largest += 1
        best.append(sorted(clique))
        if len(best) > KEEP_AT_MOST:
            best = _best(best, k)
    best = _best(best, k)

    result = []
    for rank, members in enumerate(best, 1):
        sub_id = store.subgraph(graph_id, members, f"Maximal clique #{rank} ({len(members)} nodes) of '{graph_id}'")
        result.append({"rank": rank, "size": len(members), "graph_id": sub_id,
                       "members": [node_ref(g, n) for n in members]})
    top_id = result[0]["graph_id"]

    where = f"'{graph_id}'"
    if node is not None and largest == 1:
        summary = f"{g.label(node)} ({node}) has no neighbours in {where}, so its only maximal clique is itself."
    elif node is not None:
        summary = (f"{g.label(node)} ({node}) belongs to {_plural(count, 'maximal clique')} in {where}; the largest "
                   f"has {largest} nodes: {_names(g, best[0])} (subgraph '{top_id}').")
    elif largest == 1:
        summary = f"{where} has no edges, so each of its {_plural(count, 'node')} is a maximal clique on its own."
    elif largest == 2:
        summary = (f"{where} has no triangles, so its largest cliques are single edges (2 nodes); "
                   f"it has {_plural(count, 'maximal clique')}.")
    else:
        summary = (f"The largest clique in {where} has {largest} nodes: {_names(g, best[0])} (subgraph "
                   f"'{top_id}'). {where} has {_plural(count, 'maximal clique')}, {n_largest:,} of the largest size.")
    if g.directed:
        summary += " Edge direction was ignored."
    return _fit(result, summary, top_id)
