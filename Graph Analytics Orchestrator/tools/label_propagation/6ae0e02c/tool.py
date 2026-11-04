"""Label propagation: find communities by letting each node adopt its neighbours' labels.

Rules (the validator checks them):
- Standard library, NumPy and graphkit only; graphs come from the store only.
- Never crashes: bad input returns error(...).
"""
import json
import random
from collections import Counter

from graphkit.contract import MAX_OUTPUT_BYTES, check_top_k, error, get_graph, node_ref, ok

# Leave headroom below the 8 KB limit for the summary and the JSON envelope.
_RESULT_BUDGET = MAX_OUTPUT_BYTES - 1500


def _check_int(value, name, minimum=None, maximum=None):
    """(value, None) if value is a whole number in range, else (None, error_dict)."""
    if isinstance(value, bool) or not isinstance(value, int):
        return None, error(f"{name} must be a whole number; got {value!r}.")
    if minimum is not None and value < minimum:
        return None, error(f"{name} must be at least {minimum}; got {value}.")
    if maximum is not None and value > maximum:
        return None, error(f"{name} must be at most {maximum}; got {value}.")
    return value, None


def _neighbour_sets(g):
    """Neighbours ignoring direction, with self-loops removed so a node cannot vote for itself."""
    return {n: set(g.undirected_neighbors(n)) - {n} for n in g.nodes()}


def _propagate(nodes, nbrs, seed, max_iter):
    """Asynchronous label propagation. Returns {node: label}."""
    labels = {n: n for n in nodes}
    order = sorted(nodes)
    random.Random(seed).shuffle(order)
    for _ in range(max_iter):
        changed = False
        for v in order:
            if not nbrs[v]:
                continue
            counts = Counter(labels[u] for u in nbrs[v])
            # Most frequent neighbour label; ties go to the smallest label id.
            best = min(counts, key=lambda lab: (-counts[lab], lab))
            if labels[v] != best:
                labels[v] = best
                changed = True
        if not changed:
            break
    return labels


def _modularity(communities, nbrs):
    """Newman modularity of an undirected partition, computed in pure Python.

    Q = sum over communities of [L_c / m - (D_c / 2m)^2], where L_c counts internal
    edges, D_c is the sum of degrees inside the community and m is the number of edges.
    """
    two_m = sum(len(nbrs[v]) for v in nbrs)
    if two_m == 0:
        return 0.0
    q = 0.0
    for members in communities:
        inside = set(members)
        internal = sum(len(nbrs[v] & inside) for v in members) / 2.0
        degree_sum = sum(len(nbrs[v]) for v in members)
        q += 2.0 * internal / two_m - (degree_sum / two_m) ** 2
    return q


def _build_entries(g, communities, sub_ids, cap):
    """One result entry per community, showing at most `cap` members each."""
    entries = []
    for i, (members, sub_id) in enumerate(zip(communities, sub_ids), 1):
        shown = members[:cap]
        entries.append({
            "community": i,
            "size": len(members),
            "graph_id": sub_id,
            "members_shown": len(shown),
            "truncated": len(shown) < len(members),
            "nodes": [node_ref(g, n) for n in shown],
        })
    return entries


def run(store, graph_id, top_k=10, seed=0, max_iter=100, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    assert g is not None  # get_graph returns a graph whenever err is None
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     "label_propagation takes graph_id, top_k, seed and max_iter.")
    k, k_err = check_top_k(top_k)
    if k_err:
        return k_err
    seed, seed_err = _check_int(seed, "seed")
    if seed_err:
        return seed_err
    max_iter, iter_err = _check_int(max_iter, "max_iter", minimum=1, maximum=1000)
    if iter_err:
        return iter_err

    nodes = g.nodes()
    if not nodes:
        return error(f"Graph '{graph_id}' has no nodes, so there are no communities to find.")

    nbrs = _neighbour_sets(g)
    labels = _propagate(nodes, nbrs, seed, max_iter)

    groups = {}
    for n in nodes:
        groups.setdefault(labels[n], []).append(n)
    communities = [sorted(members) for members in groups.values()]
    # Largest first; ties broken by the smallest node id so the order is deterministic.
    communities.sort(key=lambda members: (-len(members), members[0]))

    modularity = _modularity(communities, nbrs)

    # Decide what fits BEFORE registering subgraphs, so no subgraph is registered for a
    # community the result does not return (each store.subgraph call copies the parent's
    # edges, so registering hundreds of them would also be needlessly slow).
    shown = communities[:k]
    # Show as many members as the output budget allows: start from the full lists and
    # shrink the per-community cap until the result fits.
    cap = max(len(members) for members in shown)
    entries = _build_entries(g, shown, [None] * len(shown), cap)
    while cap > 1 and len(json.dumps(entries)) > _RESULT_BUDGET:
        cap = max(1, int(cap * 0.8))
        entries = _build_entries(g, shown, [None] * len(shown), cap)
    while len(entries) > 1 and len(json.dumps(entries)) > _RESULT_BUDGET:
        entries.pop()
    shown = shown[:len(entries)]

    sub_ids = [store.subgraph(graph_id, members,
                              f"Community {i} of '{graph_id}' ({len(members)} nodes)")
               for i, members in enumerate(shown, 1)]
    for entry, sub_id in zip(entries, sub_ids):
        entry["graph_id"] = sub_id

    largest = communities[0]
    summary = (f"Found {len(communities)} communities covering {len(nodes)} nodes in '{graph_id}' "
               f"(modularity {round(modularity, 6)}); the largest has {len(largest)} nodes.")
    # Only blame the output limit when it actually cut results that top_k asked for.
    if len(entries) < min(k, len(communities)):
        summary += f" Showing the {len(entries)} largest (output size limit)."
    elif any(e["truncated"] for e in entries):
        summary += " Member lists are shortened; use each community's graph_id for the full membership."
    if g.directed:
        summary += " Edge directions were ignored."

    return ok({"num_communities": len(communities), "modularity": round(modularity, 6),
               "communities": entries}, summary, result_graph_id=sub_ids[0])