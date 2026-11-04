"""louvain: modularity-based community detection (Blondel et al., 2008).

Repeats two phases until modularity stops improving:
  1. local moving: visit nodes in a (seeded) random order and move each to the neighbouring
     community that increases modularity the most, until no move helps;
  2. aggregation: collapse every community into one super-node and repeat on that smaller graph.

Directed graphs are treated as undirected. Each returned community is registered in the store
as a subgraph so other tools can run on it.
"""
import json
import random

from graphkit.contract import MAX_OUTPUT_BYTES, check_node, check_top_k, error, get_graph, node_ref, ok

MIN_GAIN = 1e-10       # a move must improve modularity by more than this (guards against float noise)
MAX_PASSES = 200       # safety cap on local-moving sweeps per level
OUTPUT_BUDGET = MAX_OUTPUT_BYTES - 1024  # leave head-room under the 8 KB limit
SAMPLE_SIZES = (6, 4, 2, 1, 0)           # members listed per community, shrunk until the output fits


def _build_level0(g, use_weights):
    """Symmetric weighted adjacency over node indices. adj[u][v] = weight; adj[u][u] = 2 * self-loop."""
    nodes = g.nodes()
    index = {n: i for i, n in enumerate(nodes)}
    adj = [dict() for _ in nodes]
    for u in nodes:
        for v, w in g.undirected_neighbors(u).items():
            if u == v:
                continue
            adj[index[u]][index[v]] = float(w) if use_weights else 1.0
    return nodes, adj


def _local_moving(adj, deg, m2, resolution, rng):
    """One level of phase 1. Returns (community of each node, whether any node moved)."""
    n = len(adj)
    comm = list(range(n))
    tot = list(deg)  # total degree of each community
    moved_any = False
    for _ in range(MAX_PASSES):
        order = list(range(n))
        rng.shuffle(order)
        moved = 0
        for u in order:
            ku = deg[u]
            cu = comm[u]
            links = {}  # weight from u into each neighbouring community
            for v, w in adj[u].items():
                if v != u:
                    links[comm[v]] = links.get(comm[v], 0.0) + w
            tot[cu] -= ku  # take u out of its community
            best, best_gain = cu, links.get(cu, 0.0) - resolution * tot[cu] * ku / m2
            for c in sorted(links):  # sorted: deterministic tie-breaking
                gain = links[c] - resolution * tot[c] * ku / m2
                if gain > best_gain + MIN_GAIN:
                    best, best_gain = c, gain
            tot[best] += ku
            if best != cu:
                comm[u] = best
                moved += 1
        if not moved:
            break
        moved_any = True
    return comm, moved_any


def _aggregate(adj, comm):
    """Phase 2: relabel communities 0..k-1 and build the graph whose nodes are the communities."""
    labels = {}
    for c in comm:
        if c not in labels:
            labels[c] = len(labels)
    relabelled = [labels[c] for c in comm]
    new_adj = [dict() for _ in labels]
    for u, nbrs in enumerate(adj):
        cu = relabelled[u]
        for v, w in nbrs.items():
            cv = relabelled[v]
            new_adj[cu][cv] = new_adj[cu].get(cv, 0.0) + w
    return relabelled, new_adj


def _modularity(adj, member, resolution):
    """Q = sum over communities of (inside / 2m) - resolution * (total degree / 2m)^2."""
    deg = [sum(nbrs.values()) for nbrs in adj]
    m2 = sum(deg)
    if m2 == 0:
        return 0.0
    inside, tot = {}, {}
    for u, nbrs in enumerate(adj):
        c = member[u]
        tot[c] = tot.get(c, 0.0) + deg[u]
        for v, w in nbrs.items():
            if member[v] == c:
                inside[c] = inside.get(c, 0.0) + w
    return sum(inside.get(c, 0.0) / m2 - resolution * (tot[c] / m2) ** 2 for c in tot)


def _louvain(adj0, resolution, seed):
    """Returns the final community index (0..k-1) of every original node."""
    rng = random.Random(seed)
    n = len(adj0)
    member = list(range(n))  # original node -> node of the current level
    adj = adj0
    best_member, best_q = list(range(n)), _modularity(adj0, list(range(n)), resolution)
    while True:
        deg = [sum(nbrs.values()) for nbrs in adj]
        m2 = sum(deg)
        if m2 == 0:
            break
        comm, moved = _local_moving(adj, deg, m2, resolution, rng)
        if not moved:
            break
        relabelled, adj = _aggregate(adj, comm)
        member = [relabelled[c] for c in member]
        q = _modularity(adj0, member, resolution)
        if q > best_q + 1e-7:
            best_member, best_q = list(member), q
        else:
            break
        if len(adj) == 1:  # everything merged into a single community
            break
    return best_member, best_q


def _check_params(seed, resolution, use_weights, node, g):
    if isinstance(seed, bool) or not isinstance(seed, int):
        return error(f"seed must be a whole number; got {seed!r}.")
    if isinstance(resolution, bool) or not isinstance(resolution, (int, float)) or not resolution > 0:
        return error(f"resolution must be a number greater than 0; got {resolution!r}.")
    if not isinstance(use_weights, bool):
        return error(f"use_weights must be true or false; got {use_weights!r}.")
    if node is not None:
        return check_node(g, node)
    return None


def run(store, graph_id, top_k=10, seed=0, resolution=1.0, use_weights=True, node=None, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. louvain takes graph_id, top_k, seed, "
                     f"resolution, use_weights and node.")
    k, err = check_top_k(top_k)
    if err:
        return err
    err = _check_params(seed, resolution, use_weights, node, g)
    if err:
        return err
    if g.number_of_nodes() == 0:
        return error(f"Graph '{graph_id}' has no nodes, so there are no communities to find.")
    if g.number_of_edges() == 0:
        return error(f"Graph '{graph_id}' has no edges, so every node would be its own community. "
                     f"Choose a graph with edges.")
    use_weights = use_weights and g.weighted
    nodes, adj = _build_level0(g, use_weights)
    if any(w < 0 for nbrs in adj for w in nbrs.values()):
        return error(f"Graph '{graph_id}' has negative edge weights; Louvain needs non-negative weights. "
                     f"Try use_weights=false.")

    member, q = _louvain(adj, float(resolution), seed)

    groups = {}
    for i, c in enumerate(member):
        groups.setdefault(c, []).append(nodes[i])
    # Number communities by size (largest first), ties by smallest node id, for a stable order.
    ordered = sorted((sorted(ms) for ms in groups.values()), key=lambda ms: (-len(ms), ms[0]))
    n_comm = len(ordered)
    chosen = ordered[:k]
    if node is not None and not any(node in ms for ms in chosen):
        chosen = chosen + [next(ms for ms in ordered if node in ms)]

    entries, sub_ids = [], {}
    for ms in chosen:
        idx = ordered.index(ms) + 1
        sub_id = store.subgraph(graph_id, ms, f"Louvain community {idx} of '{graph_id}'")
        sub_ids[idx] = sub_id
        entries.append({"community": idx, "graph_id": sub_id, "size": len(ms), "_members": ms})

    def build(sample):
        out = []
        for e in entries:
            row = {key: e[key] for key in ("community", "graph_id", "size")}
            if sample:
                row["members"] = [node_ref(g, n) for n in e["_members"][:sample]]
            out.append(row)
        return out

    result = {"modularity": round(q, 6), "num_communities": n_comm, "num_nodes": len(nodes)}
    for sample in SAMPLE_SIZES:
        result["communities"] = build(sample)
        if len(json.dumps(result)) <= OUTPUT_BUDGET:
            break
    if node is not None:
        c_idx = next(i for i, ms in enumerate(ordered, 1) if node in ms)
        result["node_community"] = {"node": node_ref(g, node), "community": c_idx,
                                    "graph_id": sub_ids[c_idx], "size": len(ordered[c_idx - 1])}
    while len(json.dumps(result)) > OUTPUT_BUDGET and len(result["communities"]) > 1:
        result["communities"] = result["communities"][: len(result["communities"]) // 2]

    largest_id = sub_ids[1]
    shown = len(result["communities"])
    summary = (f"Louvain found {n_comm} communities in '{graph_id}' (modularity {round(q, 4)}); "
               f"the largest has {len(ordered[0])} of {len(nodes)} nodes and is subgraph '{largest_id}'. "
               f"Showing the {shown} largest.")
    if g.directed:
        summary += " Edge directions were ignored."
    return ok(result, summary, result_graph_id=largest_id)
