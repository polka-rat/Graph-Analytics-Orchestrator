"""Color a graph greedily, using node degree to choose a deterministic order."""
import json

from graphkit.contract import (
    MAX_OUTPUT_BYTES,
    check_top_k,
    error,
    get_graph,
    node_ref,
    ok,
)


def run(store, graph_id: str, top_k: int = 10, **params) -> dict:
    graph, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}.")

    k, err = check_top_k(top_k)
    if err:
        return err

    nodes = graph.nodes()
    if not nodes:
        return error("The graph is empty, so there are no nodes to color.")

    #detecting slef-loops and returning an error if any node has a self-loop
    neighbors = {node: set(graph.undirected_neighbors(node)) for node in nodes}
    for node in nodes:
        if node in neighbors[node]:
            return error(
                f"Node '{node}' has a self-loop and cannot receive a valid graph color. "
                "Remove the self-loop or use a graph without self-loops."
            )

    order = sorted(nodes, key=lambda node: (-len(neighbors[node]), node))
    colors: dict[str, int] = {}
    for node in order:
        used = {colors[other] for other in neighbors[node] if other in colors}
        color = 1
        while color in used:
            color += 1
        colors[node] = color

    color_count = max(colors.values())
    class_sizes = [0] * color_count
    for color in colors.values():
        class_sizes[color - 1] += 1

    selected = sorted(nodes)[:k]
    assignments = [
        node_ref(graph, node, color=colors[node])
        for node in selected
    ]
    result = {
        "color_count": color_count,
        "color_class_sizes": class_sizes,
        "total_nodes": len(nodes),
        "assignments": assignments,
    }
    summary = (
        f"Greedy coloring uses {color_count} colors for {len(nodes)} nodes; "
        f"assignments for {len(assignments)} nodes are shown, ordered by node ID."
    )
    output = ok(result, summary)

    # Keep the complete coloring statistics while trimming only the optional
    # node assignment list if labels would push the response over the contract cap.
    while assignments and len(
        json.dumps(output, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ) > MAX_OUTPUT_BYTES:
        assignments.pop()
        result["assignments"] = assignments
        summary = (
            f"Greedy coloring uses {color_count} colors for {len(nodes)} nodes; "
            f"assignments for {len(assignments)} nodes are shown, ordered by node ID."
        )
        output = ok(result, summary)

    if len(json.dumps(output, ensure_ascii=False).encode("utf-8")) > MAX_OUTPUT_BYTES:
        return error(
            "The graph's coloring summary exceeds the response-size limit. "
            "Use a smaller graph."
        )
    return output
