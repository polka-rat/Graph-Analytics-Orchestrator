"""Connected components of a graph (BFS), with their sizes; registers each listed component as a subgraph.

Undirected graphs: ordinary connected components.
Directed graphs: weakly connected components (edge directions ignored); use
strongly_connected_components for components that respect direction.
"""
import json
from collections import deque

from graphkit.contract import MAX_OUTPUT_BYTES, check_node, check_top_k, error, get_graph, node_ref, ok

MEMBER_LIMITS = (10, 5, 3, 1, 0)  # members shown per component, shrunk until the output fits


def _components(g):
    """List of components (each a sorted list of node ids), via iterative BFS."""
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
    # Largest first; ties broken by smallest node id.
    comps.sort(key=lambda c: (-len(c), c[0]))
    return comps


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
    n = g.number_of_nodes()
    if n == 0:
        return error(f"Graph '{graph_id}' has no nodes, so it has no components. Use list_graphs to pick another graph.")

    comps = _components(g)
    kind = "weakly connected component" if g.directed else "connected component"

    # Which components to report: the top_k largest, plus the one holding `node` if asked.
    chosen = list(range(min(k, len(comps))))
    node_idx = None
    if node is not None:
        node_idx = next(i for i, c in enumerate(comps) if node in c)
        if node_idx not in chosen:
            chosen.append(node_idx)

    entries = []
    for i in chosen:
        c = comps[i]
        sub_id = store.subgraph(graph_id, c, f"{kind.capitalize()} #{i + 1} of '{graph_id}' ({len(c)} nodes)")
        entries.append({"rank": i + 1, "size": len(c), "fraction": round(len(c) / n, 6),
                        "graph_id": sub_id, "members": c})

    sizes = [len(c) for c in comps]
    base = {"num_components": len(comps), "largest_size": sizes[0],
            "isolated_nodes": sum(1 for s in sizes if s == 1),
            "mode": "weak (directions ignored)" if g.directed else "undirected"}

    for limit in MEMBER_LIMITS:
        listed = []
        for e in entries:
            members = e["members"]
            shown = [node_ref(g, m) for m in members[:limit]]
            if node is not None and e["rank"] == (node_idx + 1) and node not in members[:limit]:
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

    noun = "weakly connected components" if g.directed else "connected components"
    summary = (f"'{graph_id}' has {len(comps)} {noun}; the largest has {sizes[0]} of {n} nodes "
               f"({100 * sizes[0] / n:.1f}%).")
    if len(comps) == 1:
        summary = f"'{graph_id}' is {'weakly ' if g.directed else ''}connected: all {n} nodes form one component."
    if node is not None:
        summary += f" {g.label(node)} ({node}) is in component #{node_idx + 1} ({len(comps[node_idx])} nodes)."
    summary += " Full member lists are in each component's graph_id."
    return ok(result, summary, result_graph_id=entries[0]["graph_id"])
