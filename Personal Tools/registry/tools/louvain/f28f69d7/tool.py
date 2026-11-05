"""Detect communities by repeatedly optimizing and aggregating modularity."""

import json
import math
import random

from graphkit.contract import MAX_OUTPUT_BYTES, check_top_k, error, get_graph, node_ref, ok


def _add_arc(outgoing, incoming, source, target, weight):
    outgoing[source][target] = outgoing[source].get(target, 0.0) + weight
    incoming[target][source] = incoming[target].get(source, 0.0) + weight


def _modularity(outgoing, incoming, community, total_weight, resolution):
    if total_weight == 0:
        return 0.0
    total_out = {}
    total_in = {}
    internal = {}
    for node, cid in community.items():
        total_out[cid] = total_out.get(cid, 0.0) + sum(outgoing[node].values())
        total_in[cid] = total_in.get(cid, 0.0) + sum(incoming[node].values())
        for neighbor, weight in outgoing[node].items():
            if community[neighbor] == cid:
                internal[cid] = internal.get(cid, 0.0) + weight
    return sum(internal.get(cid, 0.0) / total_weight
               - resolution * ((total_out[cid] / total_weight)
                               * (total_in[cid] / total_weight))
               for cid in total_out)


def _one_level(outgoing, incoming, total_weight, resolution, rng):
    nodes = sorted(outgoing)
    community = {node: node for node in nodes}
    groups = {node: {node} for node in nodes}
    degree_out = {node: sum(outgoing[node].values()) for node in nodes}
    degree_in = {node: sum(incoming[node].values()) for node in nodes}
    total_out = degree_out.copy()
    total_in = degree_in.copy()
    next_id = max(nodes, default=-1) + 1
    moved_any = False

    while True:
        moved_this_pass = False
        visit = nodes.copy()
        rng.shuffle(visit)
        for node in visit:
            old = community[node]
            groups[old].remove(node)
            total_out[old] -= degree_out[node]
            total_in[old] -= degree_in[node]

            touching = {}
            for neighbor, weight in outgoing[node].items():
                if neighbor != node:
                    cid = community[neighbor]
                    touching[cid] = touching.get(cid, 0.0) + weight
            for neighbor, weight in incoming[node].items():
                if neighbor != node:
                    cid = community[neighbor]
                    touching[cid] = touching.get(cid, 0.0) + weight

            def score(cid):
                return (touching.get(cid, 0.0) / total_weight
                        - resolution * (
                            (degree_out[node] / total_weight)
                            * (total_in.get(cid, 0.0) / total_weight)
                            + (degree_in[node] / total_weight)
                            * (total_out.get(cid, 0.0) / total_weight)))

            best = old
            best_score = score(old)
            candidates = set(touching)
            if groups[old]:
                candidates.add(next_id)  # Leave the current group as a singleton.
            for cid in sorted(candidates):
                if cid != old and score(cid) > best_score + 1e-12:
                    best = cid
                    best_score = score(cid)

            if best == next_id:
                groups[best] = set()
                total_out[best] = 0.0
                total_in[best] = 0.0
                next_id += 1
            groups[best].add(node)
            total_out[best] += degree_out[node]
            total_in[best] += degree_in[node]
            community[node] = best
            if best != old:
                moved_this_pass = True
                moved_any = True

        if not moved_this_pass:
            return community, moved_any


def _aggregate(outgoing, community, members):
    grouped = {}
    for node, cid in community.items():
        grouped.setdefault(cid, set()).update(members[node])
    ordered = sorted(grouped, key=lambda cid: min(grouped[cid]))
    renamed = {cid: i for i, cid in enumerate(ordered)}
    new_members = {renamed[cid]: grouped[cid] for cid in ordered}
    new_out = {i: {} for i in new_members}
    new_in = {i: {} for i in new_members}
    for source, neighbors in outgoing.items():
        for target, weight in neighbors.items():
            _add_arc(new_out, new_in, renamed[community[source]],
                     renamed[community[target]], weight)
    return new_out, new_in, new_members


def run(store, graph_id, resolution=1.0, seed=0, top_k=10, **params):
    graph, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(sorted(params))}. "
                     "Use graph_id, resolution, seed, and top_k.")
    if (isinstance(resolution, bool) or not isinstance(resolution, (int, float))
            or not math.isfinite(resolution) or resolution <= 0):
        return error("resolution must be a positive finite number; try 1.0.")
    if isinstance(seed, bool) or not isinstance(seed, int):
        return error("seed must be an integer; try 0.")
    k, err = check_top_k(top_k)
    if err:
        return err

    nodes = graph.nodes()
    index = {node: i for i, node in enumerate(nodes)}
    outgoing = {i: {} for i in range(len(nodes))}
    incoming = {i: {} for i in range(len(nodes))}
    members = {i: {node} for node, i in index.items()}
    for source, target, weight in graph.edges():
        if not math.isfinite(weight) or weight < 0:
            return error("Louvain needs finite, non-negative edge weights. "
                         "Use a graph with valid non-negative weights.")
        u, v = index[source], index[target]
        _add_arc(outgoing, incoming, u, v, weight)
        if not graph.directed:
            _add_arc(outgoing, incoming, v, u, weight)

    total_weight = sum(sum(edges.values()) for edges in outgoing.values())
    if not math.isfinite(total_weight):
        return error("The total edge weight is too large to analyze. "
                     "Use a graph with smaller finite weights.")
    partition = [set([node]) for node in nodes]
    modularity = 0.0
    if total_weight > 0:
        rng = random.Random(seed)
        modularity = _modularity(outgoing, incoming,
                                 {node: node for node in outgoing},
                                 total_weight, resolution)
        while True:
            community, moved = _one_level(outgoing, incoming, total_weight,
                                          resolution, rng)
            groups = {}
            for node, cid in community.items():
                groups.setdefault(cid, set()).update(members[node])
            new_modularity = _modularity(outgoing, incoming, community,
                                         total_weight, resolution)
            if new_modularity + 1e-9 < modularity:
                break
            partition = list(groups.values())
            improvement = new_modularity - modularity
            modularity = new_modularity
            if not moved or len(groups) == len(outgoing) or improvement <= 1e-7:
                break
            outgoing, incoming, members = _aggregate(outgoing, community, members)

    partition.sort(key=lambda group: (-len(group), min(group)))
    entries = []
    for group in partition[:k]:
        ordered = sorted(group)
        sub_id = store.subgraph(graph_id, ordered,
                                f"Louvain community of {len(group)} nodes")
        entries.append({"graph_id": sub_id, "size": len(group),
                        "nodes": [node_ref(graph, node) for node in ordered]})

    result_graph_id = entries[0]["graph_id"] if entries else None
    while True:
        result = {"communities": entries, "total_communities": len(partition),
                  "modularity": round(modularity, 6)}
        summary = (f"Louvain found {len(partition)} communities in '{graph_id}' "
                   f"with modularity {result['modularity']}; showing {len(entries)}.")
        output = ok(result, summary, result_graph_id)
        if len(json.dumps(output, sort_keys=True).encode("utf-8")) <= MAX_OUTPUT_BYTES:
            return output
        largest = max(entries, key=lambda entry: len(entry["nodes"]), default=None)
        if largest is None or not largest["nodes"]:
            return error("The community result exceeds the 8 KB response limit. "
                         "Try a smaller top_k or a smaller graph.")
        largest["nodes"].pop()
