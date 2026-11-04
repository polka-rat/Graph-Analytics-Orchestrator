"""maximal_cliques: find the maximal cliques (groups where everyone is linked to everyone).

Bron-Kerbosch with Tomita pivoting: grow a clique R from candidates P, with X holding
nodes already tried; at each step skip the neighbours of a pivot u (the node of P | X
with the most neighbours in P), since any clique through them is found via u or a
non-neighbour of u. Worst case O(3^(n/3)), fast on sparse real graphs.
Directed graphs are treated as undirected (linked if an edge exists in either direction).
"""
import json

from graphkit.contract import check_node, check_top_k, error, get_graph, node_ref, ok

BYTE_BUDGET = 7800  # stay under the 8 KB output limit


def _bron_kerbosch(adj, candidates):
    """Yield every maximal clique (as a list) of the graph adj restricted to `candidates`."""
    # Iterative version, so deep recursion can never hit Python's recursion limit.
    stack = [([], set(candidates), set())]
    while stack:
        r, p, x = stack.pop()
        if not p and not x:
            yield r
            continue
        if not p:
            continue
        pivot = max(p | x, key=lambda u: len(p & adj[u]))
        for v in list(p - adj[pivot]):
            stack.append((r + [v], p & adj[v], x & adj[v]))
            p.remove(v)
            x.add(v)


def run(store, graph_id, node=None, min_size=2, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     "maximal_cliques takes graph_id, node, min_size and top_k.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if isinstance(min_size, bool) or not isinstance(min_size, int) or min_size < 1:
        return error(f"min_size must be a whole number of at least 1; got {min_size!r}.")
    if node is not None:
        err = check_node(g, node)
        if err:
            return err
    if g.number_of_nodes() == 0:
        return error(f"Graph '{graph_id}' has no nodes, so it has no cliques.")

    adj = {n: set(g.undirected_neighbors(n)) - {n} for n in g.nodes()}

    if node is None:
        cliques = list(_bron_kerbosch(adj, adj))
    else:  # cliques containing `node`: start with R = {node}, P = its neighbours
        cliques = [[node] + c for c in _bron_kerbosch(adj, adj[node])] if adj[node] else [[node]]

    total = len(cliques)
    clique_number = max(len(c) for c in cliques)
    n_largest = sum(1 for c in cliques if len(c) == clique_number)
    kept = [sorted(c) for c in cliques if len(c) >= min_size]
    if not kept:
        return error(f"No maximal clique has at least {min_size} nodes; the largest has {clique_number}. "
                     f"Lower min_size.")

    kept.sort(key=lambda c: (-len(c), c))  # biggest first, ties by member ids
    top = kept[:k]

    where = f" containing {g.label(node)}" if node else ""
    note = " (edge direction ignored)" if g.directed else ""
    summary = (f"Found {total} maximal cliques{where} in '{graph_id}'{note}. The largest has {clique_number} "
               f"members ({n_largest} clique{'s' if n_largest != 1 else ''} of that size); "
               f"the first is {', '.join(g.label(n) for n in top[0][:5])}{' and others' if len(top[0]) > 5 else ''}.")

    # "graph_id" holds a placeholder as long as a real id while the output is trimmed to size.
    result = [{"rank": i + 1, "size": len(c), "graph_id": "x" * (len(graph_id) + 8),
               "members": [node_ref(g, n) for n in c]} for i, c in enumerate(top)]
    out = ok(result, summary)
    while len(result) > 1 and len(json.dumps(out)) > BYTE_BUDGET:  # trim to the size limit
        result.pop()
        out["summary"] = summary + f" Showing the top {len(result)} cliques to stay within the 8 KB limit."
    # A single clique can still be too big to list in full: then show its first members only.
    first = result[0]
    while len(json.dumps(out)) > BYTE_BUDGET and len(first["members"]) > 1:
        first["members"].pop()
        first["members_truncated"] = True

    # Register each returned clique as a subgraph so other tools can run on it;
    # result_graph_id is the largest one.
    for entry, c in zip(result, top):
        entry["graph_id"] = store.subgraph(graph_id, c, f"Maximal clique of {len(c)} nodes in '{graph_id}'")
    return ok(result, out["summary"], result_graph_id=result[0]["graph_id"])
