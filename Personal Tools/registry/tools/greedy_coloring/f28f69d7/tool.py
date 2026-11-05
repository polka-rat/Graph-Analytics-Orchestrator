"""Color a graph with deterministic largest-degree-first greedy coloring."""

import json

from graphkit.contract import MAX_OUTPUT_BYTES, check_top_k, error, get_graph, node_ref, ok


def run(store, graph_id, top_k=100, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(sorted(params))}. Use graph_id and top_k.")
    k, err = check_top_k(top_k)
    if err:
        return err

    nodes = g.nodes()
    neighbors = {node: set(g.undirected_neighbors(node)) for node in nodes}
    if any(node in neighbors[node] for node in nodes):
        return error("A self-loop makes proper coloring impossible. Remove self-loops and try again.")

    order = sorted(nodes, key=lambda node: (-len(neighbors[node]), node))
    colors = {}
    for node in order:
        used = {colors[neighbor] for neighbor in neighbors[node] if neighbor in colors}
        color = 0
        while color in used:
            color += 1
        colors[node] = color

    assignments = [node_ref(g, node, color=colors[node]) for node in sorted(nodes)[:k]]
    num_colors = max(colors.values(), default=-1) + 1
    while True:
        result = {"num_colors": num_colors, "total_nodes": len(nodes),
                  "colors": assignments}
        summary = (f"Greedy coloring used {num_colors} colors for {len(nodes)} nodes; "
                   f"showing {len(assignments)} node assignments.")
        output = ok(result, summary)
        if len(json.dumps(output, sort_keys=True).encode("utf-8")) <= MAX_OUTPUT_BYTES:
            return output
        if not assignments:
            return error("The coloring result exceeds the 8 KB response limit. "
                         "Try a smaller graph or subgraph.")
        assignments.pop()
