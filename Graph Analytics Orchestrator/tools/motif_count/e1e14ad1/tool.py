"""motif_count: triangles, open triads and, on directed graphs, feed-forward loops and 3-cycles.

Each triangle is found once from adjacency (u < v < w, all three pairs linked); open triads then follow
from the node degrees. A feed-forward loop or cycle is three nodes joined by exactly those three
one-way edges (induced). Weights and self-loops are ignored.
"""
import json

from graphkit.contract import check_top_k, error, get_graph, node_ref, ok

SIZE_BUDGET = 7000  # bytes of JSON; the contract limit is 8 KB


def _loop_or_cycle(u, v, w, out):
    """For a triangle: 'feed_forward_loop' or 'cycle' if all three edges are one-way, else None."""
    if any(b in out[a] and a in out[b] for a, b in ((u, v), (u, w), (v, w))):
        return None  # a two-way pair: neither
    triple = {u, v, w}
    # one-way edges only: a cycle when every node has exactly one outgoing edge inside the triple
    return "cycle" if all(len(out[x] & triple) == 1 for x in triple) else "feed_forward_loop"


def run(store, graph_id, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. motif_count takes graph_id and top_k.")
    k, err = check_top_k(top_k)
    if err:
        return err

    # Neighbour sets by node index: out = who a node points to, und = linked in either direction.
    # Self-loops are not part of any pattern, so they are dropped.
    ids = g.nodes()
    index = {node: i for i, node in enumerate(ids)}
    out = [{index[v] for v in g.out_neighbors(node) if v != node} for node in ids]
    und = [{index[v] for v in g.undirected_neighbors(node) if v != node} for node in ids]

    triangles = 0
    loops_and_cycles = {"feed_forward_loop": 0, "cycle": 0}
    per_node = [0] * len(ids)  # triangles each node is in
    for u in range(len(ids)):
        for v in (x for x in und[u] if x > u):
            for w in (x for x in und[u] & und[v] if x > v):  # common neighbours: u < v < w, each triangle once
                triangles += 1
                for x in (u, v, w):
                    per_node[x] += 1
                kind = _loop_or_cycle(u, v, w, out)
                if kind:
                    loops_and_cycles[kind] += 1

    # Connected triples (two linked neighbours of one node); each triangle contains three of them.
    wedges = sum(len(s) * (len(s) - 1) // 2 for s in und)
    ranked = [(c, ids[i]) for i, c in enumerate(per_node) if c > 0]
    ranked.sort(key=lambda item: (-item[0], item[1]))  # ties broken by id
    result = {
        "triangles": triangles,
        "open_triads": wedges - 3 * triangles,
        "feed_forward_loops": loops_and_cycles["feed_forward_loop"] if g.directed else None,
        "directed_cycles": loops_and_cycles["cycle"] if g.directed else None,
        "top_nodes": [node_ref(g, node, triangles=c) for c, node in ranked[:k]],
    }
    while result["top_nodes"] and len(json.dumps(result)) + 600 > SIZE_BUDGET:
        result["top_nodes"].pop()  # long labels: list fewer nodes rather than break the 8 KB cap

    summary = f"'{graph_id}': {triangles:,} triangles, {result['open_triads']:,} open triads"
    if g.directed:
        summary += (f", {result['feed_forward_loops']:,} feed-forward loops and {result['directed_cycles']:,} "
                    f"directed 3-cycles (loops and cycles need exactly those one-way edges)")
    summary += "."
    if result["top_nodes"]:
        best = result["top_nodes"][0]
        summary += f" Node in most triangles: {best['label']} ({best['id']}, {best['triangles']:,})."
    return ok(result, summary)
