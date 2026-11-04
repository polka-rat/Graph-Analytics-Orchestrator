"""louvain: modularity-based community detection (Blondel et al. 2008).

Repeat two phases until nothing improves:
  1. local moving: visit nodes in a seeded random order and move each to the neighbouring community
     with the best modularity gain, until no move helps;
  2. aggregation: collapse every community into one node (internal edges become a self-loop) and
     run phase 1 again on the smaller graph.

Modularity gain of putting node i into community C (constant factors dropped):
     w(i, C) - resolution * tot(C) * k(i) / (2m)
where w(i, C) is the edge weight from i into C, tot(C) the sum of degrees in C, k(i) the degree of i
and m the total edge weight. Directed graphs are treated as undirected: the weights of u->v and v->u
are added. Each community is registered as a subgraph so other tools can run on it.
"""
import json
import random

from graphkit.contract import check_node, check_top_k, error, get_graph, node_ref, ok

SIZE_BUDGET = 8000   # bytes of JSON; the contract limit is 8 KB (8192)
SAMPLE_MEMBERS = 5   # highest-degree members listed per community
MAX_PASSES = 1000    # safety net; every pass strictly improves modularity, so it ends far sooner
EPS = 1e-12


def _symmetric_adjacency(g, index, use_weights):
    """(adj, loops): adj[i] = {j: weight} without self-loops, loops[i] = self-loop weight."""
    n = len(index)
    adj = [{} for _ in range(n)]
    loops = [0.0] * n
    for u, v, w in g.edges():
        w = w if use_weights else 1.0
        i, j = index[u], index[v]
        if i == j:
            loops[i] += w
        else:
            adj[i][j] = adj[i].get(j, 0.0) + w
            adj[j][i] = adj[j].get(i, 0.0) + w
    return adj, loops


def _degrees(adj, loops):
    return [sum(nbrs.values()) + 2 * loops[i] for i, nbrs in enumerate(adj)]


def _local_moving(adj, loops, resolution, order):
    """Phase 1. Returns (community of each node, whether any node moved)."""
    k = _degrees(adj, loops)
    m2 = sum(k)
    comm = list(range(len(adj)))
    total = k[:]
    moved_any = False
    for _ in range(MAX_PASSES):
        moved = 0
        for i in order:
            current = comm[i]
            weight_to = {}
            for j, w in adj[i].items():
                weight_to[comm[j]] = weight_to.get(comm[j], 0.0) + w
            total[current] -= k[i]
            best = current
            best_gain = weight_to.get(current, 0.0) - resolution * total[current] * k[i] / m2
            for c, w in weight_to.items():
                gain = w - resolution * total[c] * k[i] / m2
                if gain > best_gain + EPS:
                    best, best_gain = c, gain
            comm[i] = best
            total[best] += k[i]
            moved += best != current
        if not moved:
            break
        moved_any = True
    return comm, moved_any


def _aggregate(adj, loops, comm):
    """Phase 2. Relabels communities 0..c-1 (by first member) and builds the community graph."""
    label = {}
    for c in comm:
        label.setdefault(c, len(label))
    new_comm = [label[c] for c in comm]
    size = len(label)
    new_adj = [{} for _ in range(size)]
    new_loops = [0.0] * size
    for i, nbrs in enumerate(adj):
        ci = new_comm[i]
        new_loops[ci] += loops[i]
        for j, w in nbrs.items():
            cj = new_comm[j]
            if ci == cj:
                new_loops[ci] += w / 2  # each internal edge is seen from both ends
            else:
                new_adj[ci][cj] = new_adj[ci].get(cj, 0.0) + w
    return new_comm, new_adj, new_loops


def _modularity(adj, loops, membership, resolution):
    k = _degrees(adj, loops)
    m2 = sum(k)
    inside, total = {}, {}
    for i, nbrs in enumerate(adj):
        c = membership[i]
        total[c] = total.get(c, 0.0) + k[i]
        inside[c] = inside.get(c, 0.0) + 2 * loops[i] + sum(w for j, w in nbrs.items() if membership[j] == c)
    return sum(inside[c] / m2 - resolution * (total[c] / m2) ** 2 for c in total)


def _louvain(adj, loops, resolution, seed):
    rng = random.Random(seed)
    membership = list(range(len(adj)))  # original node -> node of the current (aggregated) graph
    cur_adj, cur_loops = adj, loops
    while True:
        order = list(range(len(cur_adj)))
        rng.shuffle(order)
        comm, moved = _local_moving(cur_adj, cur_loops, resolution, order)
        if not moved:
            break
        comm, cur_adj, cur_loops = _aggregate(cur_adj, cur_loops, comm)
        membership = [comm[s] for s in membership]
    return membership


def run(store, graph_id, resolution=1.0, seed=0, top_k=10, weighted=True, node=None, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. louvain takes graph_id, resolution, "
                     f"seed, top_k, weighted and node.")
    if isinstance(resolution, bool) or not isinstance(resolution, (int, float)) or resolution <= 0:
        return error(f"resolution must be a number greater than 0 (1 is the standard value); got {resolution!r}.")
    if isinstance(seed, bool) or not isinstance(seed, int):
        return error(f"seed must be a whole number (default 0); got {seed!r}.")
    if not isinstance(weighted, bool):
        return error(f"weighted must be true or false; got {weighted!r}.")
    k_top, err = check_top_k(top_k)
    if err:
        return err
    if node is not None:
        err = check_node(g, node)
        if err:
            return err

    nodes = g.nodes()
    if g.number_of_edges() == 0:
        return error(f"Graph '{graph_id}' has no edges, so there are no communities to find.")
    use_weights = weighted and g.weighted
    index = {name: i for i, name in enumerate(nodes)}
    adj, loops = _symmetric_adjacency(g, index, use_weights)
    if any(w < 0 for nbrs in adj for w in nbrs.values()) or any(w < 0 for w in loops):
        return error(f"Graph '{graph_id}' has negative edge weights, which Louvain cannot use. "
                     f"Call it again with weighted=false.")
    if sum(_degrees(adj, loops)) <= 0:
        return error(f"All edge weights in '{graph_id}' are zero. Call it again with weighted=false.")

    membership = _louvain(adj, loops, resolution, seed)
    modularity = _modularity(adj, loops, membership, resolution)

    groups = {}
    for i, c in enumerate(membership):
        groups.setdefault(c, []).append(i)
    k_deg = _degrees(adj, loops)
    # community numbers: 1 = largest; ties go to the community containing the lowest-indexed node
    numbered = list(enumerate(sorted(groups.values(), key=lambda members: (-len(members), members[0])), 1))
    total_communities = len(numbered)
    if node is not None:
        numbered = [(num, members) for num, members in numbered if index[node] in members]
    else:
        numbered = numbered[:k_top]

    def entry(members, number, gid):
        top = sorted(members, key=lambda i: (-k_deg[i], nodes[i]))[:SAMPLE_MEMBERS]
        return {"community": number, "size": len(members), "graph_id": gid,
                "top_members": [node_ref(g, nodes[i], degree=round(k_deg[i], 6)) for i in top]}

    top_size = len(numbered[0][1])
    if node is not None:
        summary = (f"{g.label(node)} is in community {numbered[0][0]} of {total_communities} "
                   f"({top_size} nodes); Louvain modularity {modularity:.4f}.")
    else:
        summary = (f"Louvain found {total_communities} communities in '{graph_id}' (modularity "
                   f"{modularity:.4f}); the largest has {top_size} of {len(nodes):,} nodes.")

    # dry run with same-length placeholder ids, to find how many communities fit in 8 KB
    placeholder = f"{graph_id.split('~')[0]}~9999"
    kept = len(numbered)
    while kept > 1 and len(json.dumps(ok([entry(m, num, placeholder) for num, m in numbered[:kept]], summary))) > SIZE_BUDGET:
        kept -= 1
    if kept < len(numbered):
        summary += f" Only the {kept} largest are listed to stay under the 8 KB output limit."

    result = []
    for num, members in numbered[:kept]:
        sub_id = store.subgraph(graph_id, [nodes[i] for i in sorted(members)],
                                f"Louvain community {num} of '{graph_id}' ({len(members)} nodes)")
        result.append(entry(members, num, sub_id))
    return ok(result, summary, result_graph_id=result[0]["graph_id"])
