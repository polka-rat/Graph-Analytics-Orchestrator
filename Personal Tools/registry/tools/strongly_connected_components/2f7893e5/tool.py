import json

from graphkit.contract import MAX_OUTPUT_BYTES, check_node, check_top_k, error, get_graph, node_ref, ok

MAX_LISTED_NODES = 10


def tarjan_scc(g):
    index = {}
    low = {}
    on_stack = set()
    stack = []
    components = []
    counter = 0

    for root in g.nodes():
        if root in index:
            continue
        index[root] = low[root] = counter
        counter += 1
        stack.append(root)
        on_stack.add(root)
        work = [(root, iter(g.out_neighbors(root)))]

        while work:
            v, nbrs = work[-1]
            descended = False
            for w in nbrs:
                if w not in index:
                    index[w] = low[w] = counter
                    counter += 1
                    stack.append(w)
                    on_stack.add(w)
                    work.append((w, iter(g.out_neighbors(w))))
                    descended = True
                    break
                if w in on_stack:
                    low[v] = min(low[v], index[w])
            if descended:
                continue

            work.pop()
            if work:
                parent = work[-1][0]
                low[parent] = min(low[parent], low[v])
            if low[v] == index[v]:
                comp = []
                while True:
                    w = stack.pop()
                    on_stack.discard(w)
                    comp.append(w)
                    if w == v:
                        break
                components.append(comp)
    return components


def _size(result):
    return len(json.dumps(result, ensure_ascii=False).encode("utf-8"))


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
        return error(f"Graph '{graph_id}' is undirected; strongly connected components are only defined for "
                     f"directed graphs. Use connected_components for undirected graphs, or pick a directed "
                     f"graph from list_graphs.")
    if node is not None:
        err = check_node(g, node)
        if err:
            return err
    if g.number_of_nodes() == 0:
        return error(f"Graph '{graph_id}' has no nodes, so it has no components. Pick a non-empty graph.")

    components = [sorted(c) for c in tarjan_scc(g)]
    components.sort(key=lambda c: (-len(c), c[0]))
    total = len(components)

    if node is not None:
        rank = next(i for i, c in enumerate(components) if node in c)
        chosen = [(rank, components[rank])]
    else:
        chosen = list(enumerate(components[:k]))

    entries = []
    for rank, comp in chosen:
        desc = f"Strongly connected component #{rank + 1} of '{graph_id}' ({len(comp)} nodes)"
        sub_id = store.subgraph(graph_id, comp, desc)
        entries.append({"rank": rank + 1, "size": len(comp), "graph_id": sub_id,
                        "nodes": [node_ref(g, n) for n in comp[:MAX_LISTED_NODES]]})

    result = {"num_components": total, "largest_size": len(components[0]),
              "is_strongly_connected": total == 1, "components": entries}
    shown = MAX_LISTED_NODES
    while _size(result) > MAX_OUTPUT_BYTES - 1024 and shown > 1:
        shown -= 1
        for e in entries:
            e["nodes"] = e["nodes"][:shown]
    while _size(result) > MAX_OUTPUT_BYTES - 1024 and len(entries) > 1:
        entries.pop()

    n = g.number_of_nodes()
    if node is not None:
        e = entries[0]
        summary = (f"{g.label(node)} ({node}) is in strongly connected component #{e['rank']} of {total}, "
                   f"with {e['size']} nodes, registered as '{e['graph_id']}'.")
        if e["size"] == 1:
            summary += " No other node can both reach it and be reached from it."
    elif total == 1:
        summary = (f"'{graph_id}' is strongly connected: every one of its {n} nodes can reach every other. "
                   f"The component is registered as '{entries[0]['graph_id']}'.")
    else:
        singletons = sum(1 for c in components if len(c) == 1)
        summary = (f"'{graph_id}' has {total} strongly connected components ({singletons} of them single "
                   f"nodes); the largest has {len(components[0])} of {n} nodes and is registered as "
                   f"'{entries[0]['graph_id']}'.")
        if singletons == total and not any(g.has_edge(v, v) for v in g.nodes()):
            summary += " Every component is a single node, so the graph has no directed cycles."
        if len(entries) < total:
            summary += f" The {len(entries)} largest are listed."
    return ok(result, summary, result_graph_id=entries[0]["graph_id"])
