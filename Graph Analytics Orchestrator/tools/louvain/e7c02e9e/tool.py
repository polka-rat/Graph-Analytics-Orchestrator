"""louvain: modularity-based community detection (Blondel et al. 2008), written from scratch.

Phase 1 moves nodes one at a time into the neighbouring community with the best modularity gain until nothing
improves; phase 2 collapses every community into a single node; the two phases repeat until no move helps.
Random node order is controlled by `seed`; the best of several seeded restarts is kept, so the output is
deterministic. Directed graphs are treated as undirected.
"""
import json
import random
import math

from graphkit.contract import check_node, check_top_k, error, get_graph, node_ref, ok

RESTARTS = 8              # seeded restarts; the partition with the highest modularity wins
EPS = 1e-12
MAX_PASSES = 10_000
MAX_OUTPUT_BYTES = 7800   # the contract allows 8 KB; stay safely below it


# ----------------------------------------------------------------------------- the algorithm
def _one_level(adj, loops, deg, two_m, gamma, rng):
    """Phase 1. Returns (community of each node, whether any node moved)."""
    n = len(adj)
    comm = list(range(n))
    tot = list(deg)                      # total degree of each community
    order = list(range(n))
    moved_any = False
    for _ in range(MAX_PASSES):
        rng.shuffle(order)
        moved = False
        for i in order:
            k_i = deg[i]
            if k_i == 0:
                continue
            ci = comm[i]
            links = {}                   # weight from i to each neighbouring community
            for j, w in adj[i].items():
                links[comm[j]] = links.get(comm[j], 0.0) + w
            tot[ci] -= k_i               # take i out of its community, then re-insert it where it fits best
            best, best_gain = ci, links.get(ci, 0.0) - gamma * tot[ci] * k_i / two_m
            for c in sorted(links):
                if c == ci:
                    continue
                gain = links[c] - gamma * tot[c] * k_i / two_m
                if gain > best_gain + EPS:
                    best, best_gain = c, gain
            tot[best] += k_i
            comm[i] = best
            if best != ci:
                moved = True
        if not moved:
            break
        moved_any = True
    return comm, moved_any


def _aggregate(adj, loops, comm):
    """Phase 2. Collapse each community into one node. Returns (adj, loops, deg, relabelled comm)."""
    labels = {}
    for c in comm:
        labels.setdefault(c, len(labels))
    comm = [labels[c] for c in comm]
    m = len(labels)
    new_adj = [dict() for _ in range(m)]
    new_loops = [0.0] * m
    for i, nbrs in enumerate(adj):
        ci = comm[i]
        new_loops[ci] += loops[i]
        for j, w in nbrs.items():
            cj = comm[j]
            if ci == cj:
                new_loops[ci] += w / 2.0     # each internal edge is seen from both ends
            else:
                new_adj[ci][cj] = new_adj[ci].get(cj, 0.0) + w
    new_deg = [sum(a.values()) + 2.0 * lp for a, lp in zip(new_adj, new_loops)]
    return new_adj, new_loops, new_deg, comm


def _louvain(adj, loops, deg, two_m, gamma, rng):
    """Returns the final community label (0..c-1) of every original node."""
    n = len(adj)
    membership = list(range(n))
    cur_adj, cur_loops, cur_deg = adj, loops, deg
    while True:
        comm, moved = _one_level(cur_adj, cur_loops, cur_deg, two_m, gamma, rng)
        if not moved:
            break
        cur_adj, cur_loops, cur_deg, comm = _aggregate(cur_adj, cur_loops, comm)
        membership = [comm[c] for c in membership]
        if len(cur_adj) == 1:
            break
    labels = {}
    for c in membership:
        labels.setdefault(c, len(labels))
    return [labels[c] for c in membership]


def _modularity(adj, loops, deg, two_m, gamma, membership):
    inside, total = {}, {}
    for i, nbrs in enumerate(adj):
        c = membership[i]
        total[c] = total.get(c, 0.0) + deg[i]
        inside[c] = inside.get(c, 0.0) + loops[i]
        for j, w in nbrs.items():
            if membership[j] == c:
                inside[c] += w / 2.0
    m = two_m / 2.0
    return sum(inside[c] / m - gamma * (total[c] / two_m) ** 2 for c in total)


# ----------------------------------------------------------------------------- the tool
def run(store, graph_id, resolution=1.0, use_weights=True, seed=0, top_k=10, node=None, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. louvain takes graph_id, resolution, "
                     f"use_weights, seed, top_k and node.")
    if (
        isinstance(resolution, bool)
        or not isinstance(resolution, (int, float))
        or not math.isfinite(resolution)
        or resolution <= 0
    ):
        return error(
            f"resolution must be a finite positive number; got {resolution!r}."
        )
    if not isinstance(use_weights, bool):
        return error("use_weights must be true or false.")
    if isinstance(seed, bool) or not isinstance(seed, int):
        return error(f"seed must be a whole number (default 0); got {seed!r}.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if node is not None:
        err = check_node(g, node)
        if err:
            return err

    nodes = g.nodes()
    index = {v: i for i, v in enumerate(nodes)}
    weighted = use_weights and g.weighted
    adj = [dict() for _ in nodes]
    loops = [0.0] * len(nodes)
    for u in nodes:                       # directed graphs are symmetrised by undirected_neighbors
        for v, w in g.undirected_neighbors(u).items():
            w = float(w) if weighted else 1.0
            if w <= 0:
                return error(f"Graph '{graph_id}' has an edge weight <= 0; Louvain needs positive weights. "
                             f"Set use_weights=false to ignore them.")
            if u == v:
                loops[index[u]] += w
            else:
                adj[index[u]][index[v]] = w
    deg = [sum(a.values()) + 2.0 * lp for a, lp in zip(adj, loops)]
    two_m = sum(deg)
    if two_m == 0:
        return error(f"Graph '{graph_id}' has no edges, so there is nothing to cluster. "
                     f"Pick a graph or subgraph that has edges.")

    best_q, best = None, None
    for r in range(RESTARTS):
        membership = _louvain(adj, loops, deg, two_m, resolution, random.Random(seed * 1000003 + r))
        q = _modularity(adj, loops, deg, two_m, resolution, membership)
        if best_q is None or q > best_q + 1e-12:
            best_q, best = q, membership
    plain_q = _modularity(adj, loops, deg, two_m, 1.0, best)

    groups = {}
    for i, c in enumerate(best):
        groups.setdefault(c, []).append(nodes[i])
    communities = sorted(groups.values(), key=lambda members: (-len(members), min(members)))
    for members in communities:
        members.sort()

    shown_idx = list(range(min(k, len(communities))))
    if node is not None:
        node_idx = next(i for i, mem in enumerate(communities) if node in mem)
        if node_idx not in shown_idx:
            shown_idx.append(node_idx)

    def degree_of(v):
        return len(g.undirected_neighbors(v))

    entries = []
    for ci in shown_idx:
        members = communities[ci]
        sub_id = store.subgraph(graph_id, members, f"Louvain community {ci + 1} of '{graph_id}' ({len(members)} nodes)")
        hubs = sorted(members, key=lambda v: (-degree_of(v), v))
        entries.append({"community": ci + 1, "size": len(members), "graph_id": sub_id, "_hubs": hubs})

    result = {"num_communities": len(communities), "modularity": round(plain_q, 6),
              "resolution": resolution, "communities": entries, "listed": len(entries)}
    if node is not None:
        result["node_community"] = {**node_ref(g, node), "community": node_idx + 1,
                                    "size": len(communities[node_idx])}
    sample = 5
    while True:                           # fit the 8 KB limit: fewer sample members, then fewer communities
        for e in entries:
            e["members"] = [node_ref(g, v) for v in e["_hubs"][:sample]]
        view = {**result, "communities": [{k2: v for k2, v in e.items() if k2 != "_hubs"} for e in entries]}
        view["listed"] = len(entries)
        sizes_ok = len(json.dumps(view)) <= MAX_OUTPUT_BYTES - 700
        if sizes_ok or (sample == 0 and len(entries) == 1):
            break
        if sample > 1:
            sample = 3 if sample > 3 else 1
        elif sample == 1:
            sample = 0
        else:
            protected = {0}

            if node is not None:
                target = next(
                    (
                        i for i, entry in enumerate(entries)
                        if entry["community"] == node_idx + 1
                    ),
                    None,
                )
                if target is not None:
                    protected.add(target)

            removable = next(
                (
                    i for i in range(len(entries) - 1, -1, -1)
                    if i not in protected
                ),
                None,
            )

            if removable is None:
                break

            entries.pop(removable)

    result = view

    largest = communities[0]
    note = "" if g.directed is False else " (edge directions were ignored)"
    wnote = " using edge weights" if weighted else ""
    summary = (f"Louvain found {len(communities)} communities in '{graph_id}'{note}{wnote} with modularity "
               f"{result['modularity']} (above ~0.3 means clear community structure). The largest has "
               f"{len(largest)} of {len(nodes)} nodes; "
               f"{result['listed']} communit{'y is' if result['listed'] == 1 else 'ies are'} listed, each registered "
               f"as its own subgraph (graph_id), and result_graph_id is the largest.")
    return ok(result, summary, result_graph_id=entries[0]["graph_id"])
