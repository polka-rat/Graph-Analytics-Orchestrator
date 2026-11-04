"""Strongly connected components of a directed graph (iterative Kosaraju); registers each listed SCC as a subgraph."""
import json

from graphkit.contract import MAX_OUTPUT_BYTES, check_node, check_top_k, error, get_graph, node_ref, ok

MEMBER_LIMITS = (10, 5, 3, 1, 0)  # members shown per component, shrunk until the output fits


def _kosaraju(g):
    """Kosaraju's algorithm without recursion. Returns a list of SCCs (lists of node ids).

    Pass 1: DFS on the graph, recording nodes in order of finishing time.
    Pass 2: DFS on the reversed graph, taking start nodes in decreasing finishing time;
            each tree found is one strongly connected component.
    """
    nodes = sorted(g.nodes())
    succ = {u: sorted(g.out_neighbors(u)) for u in nodes}
    pred = {u: sorted(g.in_neighbors(u)) for u in nodes}  # edges of the reversed graph

    # Pass 1: finishing order. Each frame is (node, position of the next successor to look at).
    visited = set()
    order = []
    for root in nodes:
        if root in visited:
            continue
        visited.add(root)
        work = [(root, 0)]
        while work:
            u, i = work[-1]
            if i < len(succ[u]):
                work[-1] = (u, i + 1)
                v = succ[u][i]
                if v not in visited:
                    visited.add(v)
                    work.append((v, 0))
            else:
                work.pop()
                order.append(u)  # u is finished

    # Pass 2: DFS on the reversed graph in decreasing finishing time.
    assigned = set()
    sccs = []
    for root in reversed(order):
        if root in assigned:
            continue
        assigned.add(root)
        comp = []
        stack = [root]
        while stack:
            u = stack.pop()
            comp.append(u)
            for v in pred[u]:
                if v not in assigned:
                    assigned.add(v)
                    stack.append(v)
        sccs.append(sorted(comp))
    return sccs


def run(store, graph_id, top_k=10, node=None, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     f"strongly_connected_components takes graph_id, top_k and node.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if not g.directed:
        return error(f"Graph '{graph_id}' is undirected, so strongly connected components are just its "
                     f"connected components. Use connected_components instead, or pick a directed graph "
                     f"(see list_graphs).")
    if node is not None:
        err = check_node(g, node)
        if err:
            return err
    n = g.number_of_nodes()
    if n == 0:
        return error(f"Graph '{graph_id}' has no nodes. Use list_graphs to pick another graph.")

    comps = _kosaraju(g)
    comps.sort(key=lambda c: (-len(c), c[0]))  # largest first, ties by smallest node id

    chosen = list(range(min(k, len(comps))))
    node_idx = None
    if node is not None:
        node_idx = next(i for i, c in enumerate(comps) if node in c)
        if node_idx not in chosen:
            chosen.append(node_idx)

    entries = []
    for i in chosen:
        c = comps[i]
        sub_id = store.subgraph(graph_id, c, f"Strongly connected component #{i + 1} of '{graph_id}' ({len(c)} nodes)")
        entries.append({"rank": i + 1, "size": len(c), "fraction": round(len(c) / n, 6),
                        "graph_id": sub_id, "members": c})

    sizes = [len(c) for c in comps]
    base = {"num_components": len(comps), "largest_size": sizes[0],
            "singleton_components": sum(1 for s in sizes if s == 1),
            "nontrivial_components": sum(1 for s in sizes if s > 1)}

    for limit in MEMBER_LIMITS:
        listed = []
        for e in entries:
            members = e["members"]
            shown = [node_ref(g, m) for m in members[:limit]]
            if node is not None and e["rank"] == node_idx + 1 and node not in members[:limit]:
                shown.append(node_ref(g, node))
            item = {k2: v for k2, v in e.items() if k2 != "members"}
            item["members"] = shown
            item["members_truncated"] = len(members) > len(shown)
            listed.append(item)
        result = dict(base, components=listed)
        if node is not None:
            result["node_component_rank"] = node_idx + 1
        if len(json.dumps(result).encode("utf-8")) < MAX_OUTPUT_BYTES - 1200:
            break

    if len(comps) == 1:
        summary = f"'{graph_id}' is strongly connected: every one of its {n} nodes can reach every other."
    elif base["nontrivial_components"] == 0:
        summary = (f"'{graph_id}' has no directed cycles: all {n} nodes are their own strongly connected "
                   f"component, so no two nodes can reach each other.")
    else:
        summary = (f"'{graph_id}' has {len(comps)} strongly connected components; the largest has "
                   f"{sizes[0]} of {n} nodes ({100 * sizes[0] / n:.1f}%), and "
                   f"{base['singleton_components']} nodes are on their own.")
    if node is not None:
        summary += f" {g.label(node)} ({node}) is in component #{node_idx + 1} ({len(comps[node_idx])} nodes)."
    summary += " Full member lists are in each component's graph_id."
    return ok(result, summary, result_graph_id=entries[0]["graph_id"])
