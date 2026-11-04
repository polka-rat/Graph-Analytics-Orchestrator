from collections import deque
import json

from graphkit.contract import check_top_k, error, get_graph, node_ref, ok


def core_numbers(g, mode="total"):
    nodes = sorted(g.nodes())
    n = len(nodes)
    if n == 0:
        return {}

    # check self loops
    for u in nodes:
        if g.has_edge(u, u):
            raise ValueError("self loop detected")

    node_to_idx = {node: i for i, node in enumerate(nodes)}

    # neighbour lists
    adj = []
    for u in nodes:
        if mode == "total" and g.directed:
            nbr_ids = list(g.out_neighbors(u)) + list(g.in_neighbors(u))
        else:
            nbr_ids = list(g.undirected_neighbors(u))
        adj.append([node_to_idx[v] for v in nbr_ids if v != u])

    deg = [len(nbrs) for nbrs in adj]
    md = max(deg) if deg else 0

    # count nodes per degree
    bin_counts = [0] * (md + 1)
    for d in deg:
        bin_counts[d] += 1

    # start positions
    start = 0
    bin_arr = [0] * (md + 1)
    for d in range(md + 1):
        bin_arr[d] = start
        start += bin_counts[d]

    pos = [0] * n
    vert = [0] * n
    for v in range(n):
        d = deg[v]
        p = bin_arr[d]
        pos[v] = p
        vert[p] = v
        bin_arr[d] += 1

    for d in range(md, 0, -1):
        bin_arr[d] = bin_arr[d - 1]
    bin_arr[0] = 0

    for i in range(n):
        v = vert[i]
        for u in adj[v]:
            if deg[u] > deg[v]:
                du = deg[u]
                pu = pos[u]
                pw = bin_arr[du]
                w = vert[pw]
                if u != w:
                    # swap nodes
                    pos[u] = pw
                    pos[w] = pu
                    vert[pu] = w
                    vert[pw] = u
                bin_arr[du] += 1
                deg[u] -= 1

    return {nodes[v]: deg[v] for v in range(n)}


def count_components(sub):
    visited = set()
    components = 0
    for node in sub.nodes():
        if node not in visited:
            components += 1
            queue = deque([node])
            visited.add(node)
            while queue:
                curr = queue.popleft()
                for nbr in sub.undirected_neighbors(curr):
                    if nbr not in visited:
                        visited.add(nbr)
                        queue.append(nbr)
    return components


def make_summary(gid, sel_k, max_k, n_sel, m_sel, dens, comp_cnt, mode, is_dir, n_top, n_total, trunc):
    dir_note = " (directed subgraph)" if is_dir else ""
    if trunc:
        return f"{sel_k}-core of '{gid}' (mode={mode}{dir_note}) has {n_sel} nodes, {m_sel} edges, {comp_cnt} component(s), density {dens:.6f}; max core is {max_k} (preview shows {n_top} of {n_total} nodes)."
    return f"{sel_k}-core of '{gid}' (mode={mode}{dir_note}) has {n_sel} nodes, {m_sel} edges, {comp_cnt} component(s), density {dens:.6f}; max core is {max_k}."


def run(store, graph_id, k=None, top_k=10, mode="total", **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err

    if params:
        return error(f"Unknown parameter(s): {', '.join(sorted(params))}.")

    if not isinstance(mode, str) or mode not in ("total", "undirected"):
        return error("mode must be 'total' or 'undirected'.")

    if k is not None:
        if isinstance(k, bool) or not isinstance(k, int) or k < 0:
            return error("k must be a non-negative integer.")

    num_top, err = check_top_k(top_k)
    if err:
        return err

    if g.number_of_nodes() == 0:
        return error("Graph is empty.")

    for u in g.nodes():
        if g.has_edge(u, u):
            return error("Graph contains self-loops.")

    try:
        cores = core_numbers(g, mode=mode)
        max_core = max(cores.values()) if cores else 0

        if k is not None and k > max_core:
            return error(f"k ({k}) exceeds maximum core number ({max_core}).")

        selected_k = k if k is not None else max_core

        selected = [n for n in g.nodes() if cores[n] >= selected_k]
        desc = f"{selected_k}-core of {graph_id} (mode={mode})"
        sub_id = store.subgraph(graph_id, sorted(selected), desc)
        sub = store.get(sub_id)

        n_sel = sub.number_of_nodes()
        m_sel = sub.number_of_edges()

        if n_sel < 2:
            density = 0.0
        elif sub.directed:
            density = round(float(m_sel) / (n_sel * (n_sel - 1)), 6)
        else:
            density = round((2.0 * float(m_sel)) / (n_sel * (n_sel - 1)), 6)

        comp_cnt = count_components(sub)

        dist_counts = {}
        for c in cores.values():
            dist_counts[c] = dist_counts.get(c, 0) + 1
        core_distribution = {str(c): dist_counts[c] for c in sorted(dist_counts)}

        ranked = sorted(g.nodes(), key=lambda n: (-cores[n], n))
        top_nodes = [
            node_ref(g, n, core_number=cores[n], in_selected_core=(cores[n] >= selected_k))
            for n in ranked[:num_top]
        ]
        preview_truncated = len(top_nodes) < g.number_of_nodes()

        res = {
            "selected_k": selected_k,
            "max_core_number": max_core,
            "mode": mode,
            "selected_node_count": n_sel,
            "selected_edge_count": m_sel,
            "density": density,
            "component_count": comp_cnt,
            "core_distribution": core_distribution,
            "top_nodes": top_nodes,
            "preview_truncated": preview_truncated,
        }

        total_nodes = g.number_of_nodes()
        summary = make_summary(
            graph_id, selected_k, max_core, n_sel, m_sel, density, comp_cnt,
            mode, sub.directed, len(top_nodes), total_nodes, preview_truncated
        )
        out = ok(res, summary, result_graph_id=sub_id)

        # size guard
        while len(json.dumps(out).encode("utf-8")) > 7500 and top_nodes:
            top_nodes.pop()
            res["preview_truncated"] = True
            out["summary"] = make_summary(
                graph_id, selected_k, max_core, n_sel, m_sel, density, comp_cnt,
                mode, sub.directed, len(top_nodes), total_nodes, True
            )

        if len(json.dumps(out).encode("utf-8")) > 8192:
            return error("Response size exceeds limit.")

        return out
    except Exception as exc:
        return error(f"Computation failed: {exc}")
