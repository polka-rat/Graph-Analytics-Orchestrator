"""degree_centrality: rank nodes by how many connections they have (degree centrality).

Score = degree / (n - 1), the same normalisation as NetworkX's degree_centrality.
On directed graphs the degree is in-degree + out-degree by default, and the ranking
can also be done by in-degree or out-degree alone. Runs in O(n + m) time.
"""
import json

from graphkit.contract import MAX_OUTPUT_BYTES, check_top_k, error, get_graph, node_ref, ok

_DIRECTIONS = ("total", "in", "out")


def run(store, graph_id, top_k=10, direction="total", **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     f"degree_centrality takes graph_id, top_k and direction.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if direction not in _DIRECTIONS:
        return error(f"direction must be one of {', '.join(_DIRECTIONS)}; got {direction!r}.")

    nodes = g.nodes()
    n = len(nodes)
    if n == 0:
        return error(f"Graph '{graph_id}' has no nodes, so there is nothing to rank.")

    # Raw degree counts. A self-loop adds 2 to an undirected degree (as in NetworkX).
    out_deg, in_deg = {}, {}
    for v in nodes:
        out_nbrs = g.out_neighbors(v)
        out_deg[v] = len(out_nbrs)
        in_deg[v] = len(g.in_neighbors(v))
        if not g.directed and v in out_nbrs:
            out_deg[v] += 1
            in_deg[v] = out_deg[v]

    if g.directed:
        total = {v: in_deg[v] + out_deg[v] for v in nodes}
        used = {"total": total, "in": in_deg, "out": out_deg}[direction]
    else:
        total = out_deg
        used = total  # in/out are the same as degree when edges have no direction

    # Highest degree first; ties broken by node id (ascending) for determinism.
    ranked = sorted(nodes, key=lambda v: (-used[v], v))[:k]
    denom = n - 1
    entries = []
    for v in ranked:
        score = round(used[v] / denom, 6) if denom > 0 else 1.0
        if g.directed:
            entries.append(node_ref(g, v, score=score, degree=total[v],
                                    in_degree=in_deg[v], out_degree=out_deg[v]))
        else:
            entries.append(node_ref(g, v, score=score, degree=total[v]))

    # Keep the whole response under the size limit (long labels with a large top_k).
    shown = len(entries)
    while shown > 1 and len(json.dumps(entries[:shown])) > MAX_OUTPUT_BYTES - 1500:
        shown -= 1
    entries = entries[:shown]

    what = {"total": "degree", "in": "in-degree", "out": "out-degree"}[direction] if g.directed else "degree"
    best = entries[0]
    summary = (f"{best['label']} ({best['id']}) has the highest {what} centrality "
               f"({best['score']}, raw count {used[best['id']]}) among {n} nodes.")
    if shown < len(ranked):
        summary += f" Output shortened to the top {shown} to stay within the size limit."
    return ok(entries, summary)
