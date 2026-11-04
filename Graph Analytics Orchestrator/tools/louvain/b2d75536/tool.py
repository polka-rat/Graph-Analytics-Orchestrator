"""louvain: communities found by greedily maximising modularity.

Author: b2d75536. Hard tier, community category.

The Louvain method repeats two phases:

1. Local moving. Every node is put in its own community, then each node in turn
   moves to the neighbouring community that raises modularity most, until no
   single move helps.
2. Aggregation. Each community becomes one node of a smaller weighted graph,
   with the edges inside it kept as a self-loop. Phase 1 runs again on that
   graph.

Modularity compares the weight inside each community with the weight expected if
the same nodes kept their degrees but were wired at random:

    Q = sum_c [ L_c / m  -  resolution * (k_c / 2m)^2 ]

where L_c is the weight inside community c, k_c the total degree of its nodes
and m the total edge weight. Edge weights are used; a directed graph is first
made undirected by adding the weight of each direction, since modularity is
defined for undirected graphs.

The order in which nodes are visited is shuffled, so the `seed` parameter fixes
it and the tool is deterministic.
"""
import json
import random

from graphkit.contract import MAX_OUTPUT_BYTES, check_top_k, error, get_graph, node_ref, ok

EPSILON = 1e-12
MAX_PASSES = 50      # local-moving sweeps per level
MAX_LEVELS = 20      # aggregation levels
MEMBERS_PER_COMMUNITY = 5


def _adjacency(g):
    """Undirected weighted adjacency {node: {neighbour: weight}}; both directions are added up."""
    adj = {n: {} for n in g.nodes()}
    for u, v, w in g.edges():
        if u == v:
            adj[u][u] = adj[u].get(u, 0.0) + w
            continue
        adj[u][v] = adj[u].get(v, 0.0) + w
        adj[v][u] = adj[v].get(u, 0.0) + w
    return adj


def _degrees(adj):
    """Weighted degree of each node; a self-loop counts twice, as modularity requires."""
    return {n: sum(nbrs.values()) + nbrs.get(n, 0.0) for n, nbrs in adj.items()}


def _local_moving(adj, degree, m2, resolution, rng):
    """Move nodes between communities while that raises modularity. Returns {node: community}."""
    community = {n: i for i, n in enumerate(adj)}
    total = {i: degree[n] for n, i in community.items()}
    order = list(adj)
    for _ in range(MAX_PASSES):
        rng.shuffle(order)
        moves = 0
        for u in order:
            own, k_u = community[u], degree[u]
            total[own] -= k_u  # take u out before comparing, so staying is judged like any other move
            links = {}
            for v, w in adj[u].items():
                if v != u:
                    links[community[v]] = links.get(community[v], 0.0) + w
            best, best_gain = own, links.get(own, 0.0) - resolution * total[own] * k_u / m2
            for c, w in links.items():
                gain = w - resolution * total[c] * k_u / m2
                if gain > best_gain + EPSILON or (gain > best_gain - EPSILON and c < best):
                    best, best_gain = c, gain
            total[best] += k_u
            community[u] = best
            moves += best != own
        if not moves:
            break
    return community


def _aggregate(adj, community):
    """One node per community; edges inside a community become its self-loop."""
    new_adj = {c: {} for c in sorted(set(community.values()))}
    for u, nbrs in adj.items():
        cu = community[u]
        row = new_adj[cu]
        for v, w in nbrs.items():
            cv = community[v]
            # Inside one community every pair shows up twice in the symmetric adjacency,
            # a self-loop only once, so halve the former to count each edge once.
            row[cv] = row.get(cv, 0.0) + (w if (cv != cu or u == v) else w / 2.0)
    return new_adj


def _modularity(adj, degree, m2, partition, resolution):
    inside, total = {}, {}
    for u, nbrs in adj.items():
        c = partition[u]
        total[c] = total.get(c, 0.0) + degree[u]
        for v, w in nbrs.items():
            if partition[v] == c:
                inside[c] = inside.get(c, 0.0) + (w if u == v else w / 2.0)
    return sum(2.0 * inside.get(c, 0.0) / m2 - resolution * (t / m2) ** 2 for c, t in total.items())


def _partition(adj, degree, m2, resolution, seed):
    """Run Louvain and return ({node: community}, number of levels used)."""
    rng = random.Random(seed)
    level_adj, level_degree, levels = adj, degree, []
    for _ in range(MAX_LEVELS):
        community = _local_moving(level_adj, level_degree, m2, resolution, rng)
        if len(set(community.values())) == len(level_adj):
            break  # nothing merged at this level, so no later level can merge either
        levels.append(community)
        level_adj = _aggregate(level_adj, community)
        level_degree = _degrees(level_adj)
    if not levels:
        return {n: i for i, n in enumerate(adj)}, 0
    final = dict(levels[0])
    for community in levels[1:]:
        final = {n: community[c] for n, c in final.items()}
    return final, len(levels)


def _fits(result, summary, result_graph_id):
    """True if this output stays inside the 8 KB the contract allows."""
    text = json.dumps(ok(result, summary, result_graph_id), allow_nan=False, sort_keys=True)
    return len(text.encode("utf-8")) <= MAX_OUTPUT_BYTES


def run(store, graph_id, resolution=1.0, seed=0, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. louvain takes graph_id, resolution, "
                     f"seed and top_k.")
    if isinstance(resolution, bool) or not isinstance(resolution, (int, float)) or not 0 < resolution <= 100:
        return error(f"resolution must be a number greater than 0 and at most 100; got {resolution!r}. "
                     f"Use 1.0 for standard modularity, higher for smaller communities.")
    if isinstance(seed, bool) or not isinstance(seed, int):
        return error(f"seed must be a whole number; got {seed!r}. It only fixes the node order, "
                     f"so any value gives a valid answer.")
    limit, err = check_top_k(top_k)
    if err:
        return err
    if g.number_of_edges() == 0:
        return error(f"Graph '{graph_id}' has no edges, so it has no communities to find. "
                     f"Use list_graphs to pick a graph with edges.")

    adj = _adjacency(g)
    degree = _degrees(adj)
    m2 = sum(degree.values())
    partition, levels = _partition(adj, degree, m2, float(resolution), seed)
    quality = _modularity(adj, degree, m2, partition, float(resolution))

    groups = {}
    for node, community in partition.items():
        groups.setdefault(community, []).append(node)
    # Largest first; ties by the smallest member id, so the ranking never depends on dict order.
    ranked = sorted((sorted(members) for members in groups.values()), key=lambda m: (-len(m), m[0]))

    shown = ranked[:limit]
    communities, largest_id = [], None
    for rank, members in enumerate(shown, 1):
        sub_id = store.subgraph(graph_id, members, f"Louvain community {rank} of '{graph_id}'")
        sub = store.get(sub_id)
        member_set = set(members)
        inside = {n: sum(1 for v in adj[n] if v != n and v in member_set) for n in members}
        best = sorted(members, key=lambda n: (-inside[n], n))
        communities.append({
            "rank": rank,
            "size": len(members),
            "internal_edges": sub.number_of_edges(),
            "graph_id": sub_id,
            "members": [node_ref(g, n, links_inside=inside[n]) for n in best[:MEMBERS_PER_COMMUNITY]],
        })
        if rank == 1:
            largest_id = sub_id

    sizes = [len(members) for members in ranked]
    result = {
        "communities_found": len(ranked),
        "modularity": round(quality, 6),
        "resolution": float(resolution),
        "seed": seed,
        "levels": levels,
        "largest_community_size": sizes[0],
        "smallest_community_size": sizes[-1],
        "communities_shown": len(communities),
        "communities": communities,
    }
    found = f"{len(ranked)} communities" if len(ranked) != 1 else "a single community"
    summary = (f"Louvain split the {g.number_of_nodes()} nodes of '{graph_id}' into {found} with "
               f"modularity {result['modularity']:.3f} (above about 0.3 means clear community "
               f"structure). The largest has {sizes[0]} nodes and is registered as graph '{largest_id}'.")

    # Keep the response inside 8 KB: show fewer members, then fewer communities.
    for per_community in range(MEMBERS_PER_COMMUNITY, -1, -1):
        for entry in result["communities"]:
            del entry["members"][per_community:]
        if _fits(result, summary, largest_id):
            break
    while len(result["communities"]) > 1 and not _fits(result, summary, largest_id):
        result["communities"].pop()
        result["communities_shown"] = len(result["communities"])
    return ok(result, summary, result_graph_id=largest_id)
