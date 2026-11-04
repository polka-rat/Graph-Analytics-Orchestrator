"""Counts 3-node patterns: the 16-type triad census for directed graphs, triangles and open triads for undirected ones.

Rules (the validator checks them):
- Implement the algorithm yourself: standard library, NumPy and graphkit only.
- Get graphs only from the store; never open files, print, or use the network.
- Never crash: return error("what went wrong and how to fix it") instead.
- Return every node as node_ref(g, node, ...), so it has both an id and a label.
- Keep the output under 8 KB: respect top_k.
- Be deterministic: same input, same output. Randomised algorithms take a `seed` parameter (default 0).
"""
from graphkit.contract import check_top_k, error, get_graph, node_ref, ok

TRICODES = (1, 2, 2, 3, 2, 4, 6, 8, 2, 6, 5, 7, 3, 8, 7, 11, 2, 6, 4, 8, 5, 9, 9, 13, 6, 10, 9, 14, 7, 14, 12, 15,
            2, 5, 6, 7, 6, 9, 10, 14, 4, 9, 9, 12, 8, 13, 14, 15, 3, 7, 8, 11, 7, 12, 14, 15, 8, 14, 13, 15, 11, 15, 15, 16)
TRIAD_NAMES = ("003", "012", "102", "021D", "021U", "021C", "111D", "111U",
               "030T", "030C", "201", "120D", "120U", "120C", "210", "300")
TRICODE_TO_NAME = {i: TRIAD_NAMES[c - 1] for i, c in enumerate(TRICODES)}
DESCRIPTIONS = {
    "003": "empty", "012": "single_edge", "102": "mutual_edge", "021D": "fan_out", "021U": "fan_in",
    "021C": "chain", "111D": "mutual_edge_with_in_edge", "111U": "mutual_edge_with_out_edge",
    "030T": "feed_forward_loop", "030C": "feedback_loop", "201": "two_mutual_edges",
    "120D": "fan_out_plus_mutual", "120U": "fan_in_plus_mutual", "120C": "chain_plus_mutual",
    "210": "almost_complete", "300": "complete",
}
CONNECTED = TRIAD_NAMES[3:]


def run(store, graph_id=None, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}.")
    k, err = check_top_k(top_k)
    if err:
        return err

    nodes = g.nodes()
    n = len(nodes)
    out = {v: set(g.out_neighbors(v)) - {v} for v in nodes}
    inn = {v: set(g.in_neighbors(v)) - {v} for v in nodes}

    if g.directed:
        order = {v: i for i, v in enumerate(nodes)}
        census = {name: 0 for name in TRIAD_NAMES}
        for v in nodes:
            vnbrs = out[v] | inn[v]
            for u in vnbrs:
                if order[u] <= order[v]:
                    continue
                neighbors = (vnbrs | out[u] | inn[u]) - {u, v}
                if u in out[v] and v in out[u]:
                    census["102"] += n - len(neighbors) - 2
                else:
                    census["012"] += n - len(neighbors) - 2
                for w in neighbors:
                    if order[u] < order[w] or (order[v] < order[w] < order[u] and w not in vnbrs):
                        code = ((u in out[v]) * 1 + (v in out[u]) * 2 + (w in out[v]) * 4
                                + (v in out[w]) * 8 + (w in out[u]) * 16 + (u in out[w]) * 32)
                        census[TRICODE_TO_NAME[code]] += 1
        census["003"] = n * (n - 1) * (n - 2) // 6 - sum(census.values())
        motifs = [{"motif": t, "name": DESCRIPTIONS[t], "count": census[t]} for t in TRIAD_NAMES]
        motifs.sort(key=lambda m: -m["count"])
        best = next(m for m in motifs if m["motif"] in CONNECTED)
        summary = f"The most common connected 3-node pattern in '{graph_id}' is {best['name']} ({best['count']} instances)."
        return ok({"motifs": motifs}, summary)

    part = {v: 0 for v in nodes}
    for u in nodes:
        for v in out[u]:
            part[u] += len(out[u] & out[v])
        part[u] //= 2
    triangles = sum(part.values()) // 3
    wedges = sum(len(out[v]) * (len(out[v]) - 1) // 2 for v in nodes)
    motifs = [{"motif": "triangle", "name": "triangle", "count": triangles},
              {"motif": "open_triad", "name": "open_triad", "count": wedges - 3 * triangles}]
    motifs.sort(key=lambda m: -m["count"])

    top = sorted(part.items(), key=lambda item: (-item[1], item[0]))[:k]
    top_nodes = [node_ref(g, v, triangles=c) for v, c in top if c > 0]

    best = motifs[0]
    summary = f"The most common 3-node pattern in '{graph_id}' is {best['name']} ({best['count']} instances)."
    if top_nodes:
        summary += f" {top_nodes[0]['label']} is part of the most triangles ({top_nodes[0]['triangles']})."
    return ok({"motifs": motifs, "top_nodes": top_nodes}, summary)
