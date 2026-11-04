import json
from graphkit.contract import check_node, check_top_k, error, get_graph, node_ref, ok


def make_summary(lbl, node, n_nbrs, n_nodes, n_edges, dens, n_prev, trunc):
    if trunc:
        return f"Ego network of {lbl} ({node}) has {n_nbrs} neighbors, {n_nodes} nodes, and {n_edges} edges with density {dens:.6f} (preview shows {n_prev} of {n_nbrs} neighbors)."
    return f"Ego network of {lbl} ({node}) has {n_nbrs} neighbors, {n_nodes} nodes, and {n_edges} edges with density {dens:.6f}."


def count_reciprocal(sub):
    count = 0
    for u in sub.nodes():
        for v in sub.out_neighbors(u):
            if u < v and sub.has_edge(v, u):
                count += 1
    return count


def run(store, graph_id, node=None, direction="out", top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err

    if params:
        return error(f"Unknown parameter(s): {', '.join(sorted(params))}.")

    if direction is None:
        direction = "out"
    elif not isinstance(direction, str) or direction not in ("both", "in", "out"):
        return error("direction must be 'both', 'in', or 'out'.")

    k, err = check_top_k(top_k)
    if err:
        return err

    err = check_node(g, node)
    if err:
        return err

    try:
        # get neighbours
        if not g.directed:
            nbr_map = g.out_neighbors(node)
        elif direction == "in":
            nbr_map = g.in_neighbors(node)
        elif direction == "out":
            nbr_map = g.out_neighbors(node)
        else:
            nbr_map = set(g.out_neighbors(node)) | set(g.in_neighbors(node))

        nbrs = set(nbr_map)
        if node in nbrs:
            nbrs.remove(node)

        # register induced subgraph
        node_list = [node] + sorted(nbrs)
        desc = f"Ego network of {node} in {graph_id} (direction={direction})"
        sub_id = store.subgraph(graph_id, node_list, desc)
        sub = store.get(sub_id)

        n_nodes = sub.number_of_nodes()
        n_edges = sub.number_of_edges()

        # density
        if n_nodes < 2:
            density = 0.0
        elif sub.directed:
            density = round(float(n_edges) / (n_nodes * (n_nodes - 1)), 6)
        else:
            density = round((2.0 * float(n_edges)) / (n_nodes * (n_nodes - 1)), 6)

        # reciprocal pairs for directed
        if sub.directed:
            reciprocal_count = count_reciprocal(sub)
        else:
            reciprocal_count = None

        # local degrees in subgraph
        local_deg = {}
        for n in nbrs:
            if sub.directed:
                deg = len(sub.out_neighbors(n)) + len(sub.in_neighbors(n))
            else:
                deg = len(sub.out_neighbors(n))
            local_deg[n] = deg

        # sort by degree descending then id ascending
        ranked = sorted(nbrs, key=lambda n: (-local_deg[n], n))

        preview = []
        for n in ranked[:k]:
            preview.append(node_ref(g, n, local_degree=local_deg[n]))

        preview_truncated = len(preview) < len(nbrs)

        dir_note = (
            "'out' selects outgoing neighbours, 'in' selects incoming neighbours, "
            "and 'both' selects their union. For undirected graphs, all three options "
            "select the same neighbours."
        )

        res = {
            "center": node_ref(g, node),
            "direction": direction,
            "direction_note": dir_note,
            "neighbor_count": len(nbrs),
            "node_count": n_nodes,
            "edge_count": n_edges,
            "density": density,
            "reciprocal_pair_count": reciprocal_count,
            "neighbors_preview": preview,
            "preview_truncated": preview_truncated,
        }

        lbl = g.label(node)
        summary = make_summary(lbl, node, len(nbrs), n_nodes, n_edges, density, len(preview), preview_truncated)
        out = ok(res, summary, result_graph_id=sub_id)

        # size guard
        while len(json.dumps(out).encode("utf-8")) > 7500 and preview:
            preview.pop()
            res["preview_truncated"] = True
            out["summary"] = make_summary(lbl, node, len(nbrs), n_nodes, n_edges, density, len(preview), True)

        if len(json.dumps(out).encode("utf-8")) > 8192:
            return error("Response size exceeds limit.")

        return out
    except Exception as exc:
        return error(f"Computation failed: {exc}")
