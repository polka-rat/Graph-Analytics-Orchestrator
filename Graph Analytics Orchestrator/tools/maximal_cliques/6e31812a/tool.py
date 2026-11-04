"""Finds the maximal cliques of a graph (groups where every pair of nodes is connected) and returns the largest.

Algorithm: Bron-Kerbosch with pivoting (Tomita et al., 2006). It grows a clique R from candidate set P,
with X holding nodes already tried. At each call it picks a pivot u in P | X with the most neighbours
in P, and only branches on candidates that are NOT neighbours of u: every maximal clique still gets
found exactly once, but far fewer branches are explored. Worst case O(3^(V/3)), which is optimal
because a graph can have that many maximal cliques; on sparse real graphs it is fast.

Directed graphs are treated as undirected: an edge in either direction connects two nodes
(mutual_only=true keeps only pairs linked both ways). Self-loops are ignored. Weights are ignored.
"""
import json

from graphkit.contract import MAX_OUTPUT_BYTES, check_node, check_top_k, error, get_graph, node_ref, ok

SIZE_MARGIN = 900  # bytes kept free for the summary sentence and the counts


def _adjacency(g, mutual_only):
    adj = {}
    for n in g.nodes():
        if g.directed and mutual_only:
            nbrs = set(g.out_neighbors(n)) & set(g.in_neighbors(n))
        else:
            nbrs = set(g.undirected_neighbors(n))
        nbrs.discard(n)  # ignore self-loops
        adj[n] = nbrs
    return adj


def _bron_kerbosch(adj, r, p, x, out):
    """Appends every maximal clique that extends r (using candidates p, excluding x) to out."""
    if not p and not x:
        out.append(r)
        return
    # Pivot: the node of P | X with the most neighbours in P (ties broken by id for determinism).
    pivot = max(p | x, key=lambda u: (len(p & adj[u]), u))
    for v in sorted(p - adj[pivot]):
        _bron_kerbosch(adj, r + [v], p & adj[v], x & adj[v], out)
        p.discard(v)
        x.add(v)


def _size(obj):
    return len(json.dumps(obj, allow_nan=False, sort_keys=True).encode("utf-8"))


def run(store, graph_id, top_k=10, node=None, mutual_only=False, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     f"maximal_cliques takes graph_id, top_k, node and mutual_only.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if not isinstance(mutual_only, bool):
        return error(f"mutual_only must be true or false; got {mutual_only!r}.")
    if node is not None:
        err = check_node(g, node)
        if err:
            return err
    if g.number_of_nodes() == 0:
        return error(f"Graph '{graph_id}' has no nodes, so it has no cliques. "
                     f"Use list_graphs to pick a non-empty graph.")

    adj = _adjacency(g, mutual_only)
    cliques = []
    if node is None:
        _bron_kerbosch(adj, [], set(adj), set(), cliques)
    else:  # only the maximal cliques that contain this node
        _bron_kerbosch(adj, [node], set(adj[node]), set(), cliques)

    # Largest first; ties broken by the sorted member ids, so the order is deterministic.
    cliques = sorted((sorted(c) for c in cliques), key=lambda c: (-len(c), c))
    omega = len(cliques[0])
    n_largest = sum(1 for c in cliques if len(c) == omega)

    result = {
        "graph_id": graph_id,
        "node": node_ref(g, node) if node is not None else None,
        "clique_number": omega,
        "maximal_cliques": len(cliques),
        "largest_cliques": n_largest,
        "requested": k,
        "returned": 0,
        "cliques": [],
    }
    # Add cliques (largest first) while the whole response stays under the 8 KB limit.
    for i, members in enumerate(cliques[:k]):
        entry = {"rank": i + 1, "size": len(members), "graph_id": None,
                 "members": [node_ref(g, m) for m in members], "members_truncated": False}
        result["cliques"].append(entry)
        if _size(result) > MAX_OUTPUT_BYTES - SIZE_MARGIN:
            if i > 0:  # no room for this clique: stop here
                result["cliques"].pop()
                break
            while len(entry["members"]) > 1 and _size(result) > MAX_OUTPUT_BYTES - SIZE_MARGIN:
                entry["members"].pop()  # a single huge clique: list as many members as fit
            entry["members_truncated"] = True
    for entry in result["cliques"]:
        members = cliques[entry["rank"] - 1]
        entry["graph_id"] = store.subgraph(graph_id, members, f"Maximal clique #{entry['rank']} of "
                                           f"'{graph_id}' ({len(members)} nodes)")
    result["returned"] = len(result["cliques"])

    best = result["cliques"][0]
    names = ", ".join(m["label"] for m in best["members"][:6]) + (", ..." if best["size"] > 6 else "")
    scope = f"containing {g.label(node)} ({node})" if node is not None else f"in '{graph_id}'"
    direction = (" Directions were ignored (an edge either way counts)." if g.directed and not mutual_only
                 else " Only pairs linked in both directions count." if g.directed else "")
    shown = (f" Showing {result['returned']} of the {k} requested to stay within the size limit."
             if result["returned"] < min(k, len(cliques)) else "")
    summary = (f"The largest group {scope} where everyone is directly connected to everyone has {omega} nodes "
               f"({names}). There are {len(cliques)} maximal cliques {scope}, {n_largest} of them of size "
               f"{omega}.{direction}{shown}")
    return ok(result, summary, result_graph_id=best["graph_id"])
