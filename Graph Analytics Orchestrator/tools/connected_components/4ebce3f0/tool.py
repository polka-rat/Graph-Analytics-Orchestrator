"""Finds the connected components of a graph and their sizes (weakly connected on directed graphs).

Algorithm: breadth-first search from every node not yet visited, ignoring edge direction.
Each search collects one component. Time O(V + E), memory O(V).
"""
import json
from collections import deque

from graphkit.contract import MAX_OUTPUT_BYTES, check_node, check_top_k, error, get_graph, node_ref, ok

MEMBER_CAPS = (10, 5, 3, 1, 0)  # how many member nodes to list per component, tried in order until it fits


def _components(g):
    """All components as sorted lists of node ids, largest first (ties: smallest node id first)."""
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
            for v in g.undirected_neighbors(u):
                if v not in seen:
                    seen.add(v)
                    comp.append(v)
                    queue.append(v)
        comps.append(sorted(comp))
    comps.sort(key=lambda c: (-len(c), c[0]))
    return comps


def _build(g, comps, shown, sub_ids, cap, n_comps, mode, node, node_idx):
    entries = []
    for i, comp in enumerate(comps[:shown]):
        entries.append({
            "component": i + 1,
            "size": len(comp),
            "graph_id": sub_ids[i],
            "members": [node_ref(g, n) for n in comp[:cap]],
            "members_shown": min(cap, len(comp)),
        })
    result = {
        "num_components": n_comps,
        "connectivity": mode,
        "largest_size": len(comps[0]),
        "isolated_nodes": sum(1 for c in comps if len(c) == 1),
        "components_shown": shown,
        "components": entries,
    }
    if node is not None:
        result["node"] = node_ref(g, node, component=node_idx + 1, component_size=len(comps[node_idx]))
    return result


def run(store, graph_id, top_k=10, node=None, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     f"connected_components takes graph_id, top_k and node.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if node is not None:
        err = check_node(g, node)
        if err:
            return err
    if g.number_of_nodes() == 0:
        return error(f"Graph '{graph_id}' has no nodes, so it has no components. "
                     f"Use list_graphs to pick a non-empty graph.")

    comps = _components(g)
    n_comps = len(comps)
    mode = "weak" if g.directed else "undirected"
    node_idx = None
    if node is not None:
        node_idx = next(i for i, c in enumerate(comps) if node in c)

    # Register the components we return (plus the node's own component) as subgraphs.
    shown = min(k, n_comps)
    word = "Weakly connected component" if g.directed else "Connected component"
    sub_ids = {}
    for i in range(shown):
        sub_ids[i] = store.subgraph(graph_id, comps[i], f"{word} {i + 1} of '{graph_id}' ({len(comps[i])} nodes)")
    if node_idx is not None and node_idx not in sub_ids:
        sub_ids[node_idx] = store.subgraph(graph_id, comps[node_idx],
                                           f"{word} of '{graph_id}' containing {node} ({len(comps[node_idx])} nodes)")

    # Keep the output under the 8 KB limit: list fewer members, then fewer components, if needed.
    budget = MAX_OUTPUT_BYTES - 1200  # room for the summary and the other keys
    result = None
    for cap in MEMBER_CAPS:
        result = _build(g, comps, shown, sub_ids, cap, n_comps, mode, node, node_idx)
        if len(json.dumps(result).encode("utf-8")) <= budget:
            break
    while shown > 1 and len(json.dumps(result).encode("utf-8")) > budget:
        shown -= 1
        result = _build(g, comps, shown, sub_ids, 0, n_comps, mode, node, node_idx)

    kind = "weakly connected component" if g.directed else "connected component"
    plural = "" if n_comps == 1 else "s"
    biggest = comps[0]
    summary = (f"'{graph_id}' has {n_comps} {kind}{plural}"
               f"{' (edge direction ignored)' if g.directed else ''}; the largest has "
               f"{len(biggest)} of {g.number_of_nodes()} nodes")
    if n_comps == 1:
        summary = (f"'{graph_id}' is {'weakly ' if g.directed else ''}connected: all "
                   f"{g.number_of_nodes()} nodes form one component")
    if node is not None:
        summary += (f". {g.label(node)} ({node}) is in component {node_idx + 1}, "
                    f"which has {len(comps[node_idx])} nodes")
        result_graph_id = sub_ids[node_idx]
    else:
        result_graph_id = sub_ids[0]
    summary += f". Subgraph '{result_graph_id}' holds that component."
    return ok(result, summary, result_graph_id=result_graph_id)