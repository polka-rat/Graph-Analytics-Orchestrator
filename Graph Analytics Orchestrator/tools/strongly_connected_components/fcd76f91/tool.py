"""strongly_connected_components: groups of nodes that can all reach each other.

Uses Tarjan's algorithm. I wrote the DFS with an explicit stack instead of
recursion, because a long chain of nodes could hit Python's recursion limit.
"""
import json

from graphkit.contract import MAX_OUTPUT_BYTES, check_node, check_top_k, error, get_graph, node_ref, ok

# How many members to list per component. If the reply is too big we try the next smaller number.
MEMBER_SAMPLES = (10, 5, 3, 1, 0)
SIZE_BUDGET = MAX_OUTPUT_BYTES - 512  # keep some space for the summary


def tarjan_scc(g):
    """Return every strongly connected component as a sorted list of node ids, largest first.

    Each node gets an index (the order the DFS reaches it) and a low value (the smallest
    index it can get back to). When a node's low value equals its own index, that node
    and everything above it on the stack form one component.
    """
    index = {}
    low = {}
    stack = []
    on_stack = set()
    components = []
    counter = 0

    for start in sorted(g.nodes()):
        if start in index:
            continue
        index[start] = low[start] = counter
        counter += 1
        stack.append(start)
        on_stack.add(start)
        # each entry: (node, iterator over the neighbours it still has to look at)
        dfs = [(start, iter(sorted(g.out_neighbors(start))))]

        while dfs:
            v, neighbours = dfs[-1]
            went_deeper = False
            for w in neighbours:
                if w not in index:
                    index[w] = low[w] = counter
                    counter += 1
                    stack.append(w)
                    on_stack.add(w)
                    dfs.append((w, iter(sorted(g.out_neighbors(w)))))
                    went_deeper = True
                    break
                if w in on_stack:
                    low[v] = min(low[v], index[w])
            if went_deeper:
                continue

            # v is finished: pass its low value up to its parent
            dfs.pop()
            if dfs:
                parent = dfs[-1][0]
                low[parent] = min(low[parent], low[v])

            if low[v] == index[v]:
                comp = []
                while True:
                    w = stack.pop()
                    on_stack.discard(w)
                    comp.append(w)
                    if w == v:
                        break
                components.append(sorted(comp))

    # biggest first; if two have the same size, the one with the smaller first id comes first
    components.sort(key=lambda c: (-len(c), c[0]))
    return components


def describe(g, comp, rank, sub_id, n_members):
    return {"rank": rank, "size": len(comp), "graph_id": sub_id,
            "members": [node_ref(g, n) for n in comp[:n_members]],
            "members_truncated": len(comp) > n_members}


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
        return error(f"Graph '{graph_id}' is undirected, and strongly connected components are defined only "
                     f"for directed graphs. Use connected_components for undirected graphs, or list_graphs "
                     f"to find a directed one.")
    if node is not None:
        err = check_node(g, node)
        if err:
            return err
    if g.number_of_nodes() == 0:
        return error(f"Graph '{graph_id}' has no nodes, so it has no components. Use list_graphs to pick another.")

    components = tarjan_scc(g)
    singletons = sum(1 for c in components if len(c) == 1)
    top = components[:k]
    sub_ids = [store.subgraph(graph_id, c, f"Strongly connected component #{i} of '{graph_id}' ({len(c)} nodes)")
               for i, c in enumerate(top, 1)]

    node_rank = None
    if node is not None:
        node_rank = next(i for i, c in enumerate(components, 1) if node in c)
        node_comp = components[node_rank - 1]
        if node_rank <= k:
            node_sub = sub_ids[node_rank - 1]
        else:
            node_sub = store.subgraph(graph_id, node_comp, f"Strongly connected component of {node} "
                                                           f"in '{graph_id}' ({len(node_comp)} nodes)")

    def build(n_members, n_listed):
        result = {"num_components": len(components), "largest_size": len(components[0]),
                  "num_singletons": singletons, "is_strongly_connected": len(components) == 1,
                  "components": [describe(g, c, i, sid, n_members)
                                 for i, (c, sid) in enumerate(zip(top[:n_listed], sub_ids), 1)]}
        if node_rank is not None:
            result["node_component"] = {"node": node_ref(g, node),
                                        **describe(g, node_comp, node_rank, node_sub, n_members)}
        return result

    def fits(result):
        return len(json.dumps(result).encode("utf-8")) <= SIZE_BUDGET

    # Make the reply fit in 8 KB: first list fewer members, then list fewer components.
    n_listed = len(top)
    result = None
    while result is None:
        for n_members in MEMBER_SAMPLES:
            attempt = build(n_members, n_listed)
            if fits(attempt):
                result = attempt
                break
        else:
            n_listed -= 1
            if n_listed == 0:
                result = build(0, 0)

    largest = components[0]
    names = ", ".join(g.label(n) for n in largest[:3])
    if len(largest) > 3:
        names += ", ..."

    if len(components) == 1:
        summary = (f"'{graph_id}' is strongly connected: all {len(largest)} nodes can reach each other "
                   f"(one component, subgraph '{sub_ids[0]}').")
    elif len(largest) == 1:
        summary = (f"'{graph_id}' has no directed cycles, so no two nodes reach each other: each of its "
                   f"{len(components)} nodes is its own strongly connected component.")
    else:
        summary = (f"'{graph_id}' has {len(components)} strongly connected components; the largest has "
                   f"{len(largest)} of {g.number_of_nodes()} nodes ({names}; subgraph '{sub_ids[0]}'), and "
                   f"{singletons} node(s) are on no cycle (components of size 1).")
    if n_listed < len(top):
        summary += f" Only {n_listed} components are listed to keep the output small."
    if node_rank is not None:
        summary += (f" {g.label(node)} ({node}) is in component #{node_rank} with {len(node_comp)} node(s) "
                    f"(subgraph '{node_sub}').")

    result_graph = node_sub if node_rank is not None else sub_ids[0]
    return ok(result, summary, result_graph_id=result_graph)
