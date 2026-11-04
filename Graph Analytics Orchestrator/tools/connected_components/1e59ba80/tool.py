"""TODO: one line saying what this tool computes.

Rules (the validator checks them):
- Implement the algorithm yourself: standard library, NumPy and graphkit only.
- Get graphs only from the store; never open files, print, or use the network.
- Never crash: return error("what went wrong and how to fix it") instead.
- Return every node as node_ref(g, node, ...), so it has both an id and a label.
- Keep the output under 8 KB: respect top_k.
- Be deterministic: same input, same output. Randomised algorithms take a `seed` parameter (default 0).
"""
import json
from collections import deque

from graphkit.contract import MAX_OUTPUT_BYTES, error, get_graph, node_ref, ok

MEMBER_CAPS = (20, 10, 5, 0)
SIZE_BUDGET = MAX_OUTPUT_BYTES - 600

# BFS on each unseen vertex to find connected components
def _components(g):
    seen = set()
    comps = []
    for start in sorted(g.nodes()):
        if start in seen:
            continue
        seen.add(start)
        comp = [start]
        queue = deque([start])
        while queue:
            u = queue.popleft()
            for v in g.neighbors(u):
                if v not in seen:
                    seen.add(v)
                    comp.append(v)
                    queue.append(v)
        comps.append(sorted(comp))
    comps.sort(key=lambda c: (-len(c), c[0]))
    return comps


def _entry(g, rank, comp, sub_id, cap):
    return {"rank": rank, "size": len(comp), "graph_id": sub_id,
            "members": [node_ref(g, n) for n in comp[:cap]],
            "members_shown": min(cap, len(comp))}


def run(store, graph_id, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. connected_components takes only graph_id.")
    if g.directed:
        return error(f"Graph '{graph_id}' is directed, but connected_components works on undirected graphs only. "
                     f"Use strongly_connected_components for directed graphs, or list_graphs to pick an "
                     f"undirected graph.")
    if g.number_of_nodes() == 0:
        return error(f"Graph '{graph_id}' has no nodes, so it has no components. Use list_graphs to pick "
                     f"another graph.")

    comps = _components(g)
    n_comps = len(comps)
    base = {"num_components": n_comps,
            "is_connected": n_comps == 1,
            "largest_size": len(comps[0]),
            "num_isolated_nodes": sum(1 for c in comps if len(c) == 1)}

    placeholder = f"{graph_id.split('~')[0]}~000000"

    # Check with Size_budget to ensure output is within 8Kb
    for cap in MEMBER_CAPS:
        result = dict(base, components=[_entry(g, i, c, placeholder, cap) for i, c in enumerate(comps, 1)])
        if len(json.dumps(result).encode("utf-8")) <= SIZE_BUDGET:
            break
    while len(json.dumps(result).encode("utf-8")) > SIZE_BUDGET and len(result["components"]) > 1:
        result["components"].pop()

    for entry, comp in zip(result["components"], comps):
        entry["graph_id"] = store.subgraph(graph_id, comp, f"Connected component #{entry['rank']} of "
                                                           f"'{graph_id}' ({len(comp)} nodes)")

    if n_comps == 1:
        summary = f"'{graph_id}' is connected: all {len(comps[0])} nodes form a single connected component."
    else:
        summary = (f"'{graph_id}' has {n_comps} connected components; the largest has {len(comps[0])} of "
                   f"{g.number_of_nodes()} nodes and {base['num_isolated_nodes']} node(s) are isolated.")
    if len(result["components"]) < n_comps:
        summary += f" Only the {len(result['components'])} largest components are listed to keep the output small."
    return ok(result, summary, result_graph_id=result["components"][0]["graph_id"])

    # A tool that produces a node set or subgraph (marked with an arrow in the menu) registers it:
    #     sub_id = store.subgraph(graph_id, nodes, "Largest community of 'karate'")
    #     return ok(result, summary, result_graph_id=sub_id)
    # If it produces several node sets (e.g. communities), register each one, put its id in that
    # entry of the result as "graph_id", and return the largest one's id as result_graph_id.
