"""Maximal cliques: groups of nodes that are all connected to each other and cannot be extended.

Rules (the validator checks them):
- Standard library, NumPy and graphkit only; graphs come from the store only.
- Never crashes: bad input returns error(...).
"""
import json

from graphkit.contract import MAX_OUTPUT_BYTES, check_top_k, error, get_graph, node_ref, ok

# Leave headroom below the 8 KB limit for the summary and the JSON envelope.
_RESULT_BUDGET = MAX_OUTPUT_BYTES - 1500


def _bron_kerbosch(adj):
    """Every maximal clique of an undirected graph, using Bron-Kerbosch with pivoting.

    R is the clique being built, P the candidates that can extend it and X the nodes
    already handled. A clique is maximal when P and X are both empty. Pivoting picks
    the candidate with the most neighbours in P, which skips branches that cannot
    produce a new maximal clique.
    """
    found = []

    def expand(r, p, x):
        if not p and not x:
            found.append(sorted(r))
            return
        # Pivot: the node in P | X with the largest overlap with P.
        pivot = max(p | x, key=lambda u: len(adj[u] & p))
        for v in sorted(p - adj[pivot]):
            expand(r | {v}, p & adj[v], x & adj[v])
            p = p - {v}
            x = x | {v}

    expand(set(), set(adj), set())
    return found


def _build_entries(g, cliques, sub_ids):
    """One result entry per clique, listing every member (a clique is never truncated)."""
    return [{
        "clique": i,
        "size": len(members),
        "graph_id": sub_id,
        "nodes": [node_ref(g, n) for n in members],
    } for i, (members, sub_id) in enumerate(zip(cliques, sub_ids), 1)]


def run(store, graph_id, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     "maximal_cliques takes graph_id and top_k.")
    k, err = check_top_k(top_k)
    if err:
        return err

    if g.directed:
        return error(f"maximal_cliques needs an undirected graph, but '{graph_id}' is directed. "
                     f"Try 'karate' or 'lesmis'.")

    nodes = g.nodes()
    if not nodes:
        return error(f"Graph '{graph_id}' has no nodes, so there are no cliques to find.")

    # Self-loops are removed: a node is always connected to itself, which says nothing
    # about whether a group of distinct nodes is a clique.
    adj = {n: set(g.neighbors(n)) - {n} for n in nodes}

    cliques = _bron_kerbosch(adj)
    # Largest first; ties broken by the sorted node ids so the order is deterministic.
    cliques.sort(key=lambda members: (-len(members), members))

    # Decide how many whole cliques fit BEFORE registering subgraphs,
    # so no subgraph is registered for a clique the result does not return.
    shown = cliques[:k]
    entries = _build_entries(g, shown, [None] * len(shown))
    while len(entries) > 1 and len(json.dumps(entries)) > _RESULT_BUDGET:
        entries.pop()
    shown = shown[:len(entries)]

    sub_ids = [store.subgraph(graph_id, members,
                              f"Maximal clique {i} of '{graph_id}' ({len(members)} nodes)")
               for i, members in enumerate(shown, 1)]
    for entry, sub_id in zip(entries, sub_ids):
        entry["graph_id"] = sub_id

    largest = cliques[0]
    summary = (f"Found {len(cliques)} maximal cliques in '{graph_id}'; the largest has "
               f"{len(largest)} nodes.")
    if len(entries) < len(cliques):
        summary += f" Showing the {len(entries)} largest (output size limit)."

    return ok({"total_cliques": len(cliques), "cliques": entries}, summary,
              result_graph_id=sub_ids[0])
