"""Connected components by BFS; on directed graphs, the weakly connected components."""
import json
from collections import deque

from graphkit.contract import MAX_OUTPUT_BYTES, check_top_k, error, get_graph, node_ref, ok

SAMPLE_SIZES = (10, 5, 3, 1, 0)  # members listed per component, reduced until under 8 KB


def find_components(g):
    """Components as sorted lists of node ids, largest first."""
    seen = set()
    components = []
    for start in sorted(g.nodes()):
        if start in seen:
            continue
        seen.add(start)
        queue = deque([start])
        members = []
        while queue:
            u = queue.popleft()
            members.append(u)
            for v in g.undirected_neighbors(u):
                if v not in seen:
                    seen.add(v)
                    queue.append(v)
        components.append(sorted(members))
    components.sort(key=lambda c: (-len(c), c[0]))
    return components


def run(store, graph_id, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. connected_components takes graph_id and top_k.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if g.number_of_nodes() == 0:
        return ok({"component_count": 0, "components": []},
                  f"Graph '{graph_id}' has no nodes, so it has no components.")

    components = find_components(g)
    shown = components[:k]
    sub_ids = [store.subgraph(graph_id, members, f"Connected component {rank} of '{graph_id}'")
               for rank, members in enumerate(shown, 1)]

    def build(sample, count):
        entries = [{"rank": rank, "size": len(members), "graph_id": sub_ids[rank - 1],
                    "members": [node_ref(g, u) for u in members[:sample]],
                    "more_members": max(0, len(members) - sample)}
                   for rank, members in enumerate(shown[:count], 1)]
        result = {"component_count": len(components), "components": entries}
        return ok(result, summarize(g, graph_id, components, count), result_graph_id=sub_ids[0])

    def fits(out):
        return len(json.dumps(out, sort_keys=True).encode("utf-8")) <= MAX_OUTPUT_BYTES

    for sample in SAMPLE_SIZES:
        out = build(sample, len(shown))
        if fits(out):
            return out
    count = len(shown)
    while count > 1 and not fits(out):
        count -= 1
        out = build(0, count)
    return out


def summarize(g, graph_id, components, shown):
    n = g.number_of_nodes()
    c = len(components)
    if c == 1 and n == 1:
        text = f"'{graph_id}' has a single node, so it is one component."
    elif c == 1:
        text = f"All {n} nodes of '{graph_id}' are connected: it has a single component."
    else:
        text = (f"'{graph_id}' has {c} connected components; the largest has "
                f"{len(components[0])} of {n} nodes.")
        if shown < c:
            text += f" The {shown} largest are listed."
    if g.directed:
        text += " Edge direction was ignored (weakly connected components)."
    return text
