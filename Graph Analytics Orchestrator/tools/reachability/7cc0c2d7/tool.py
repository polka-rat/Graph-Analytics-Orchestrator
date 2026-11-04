"""TODO: one line saying what this tool computes.

Rules (the validator checks them):
- Implement the algorithm yourself: standard library, NumPy and graphkit only.
- Get graphs only from the store; never open files, print, or use the network.
- Never crash: return error("what went wrong and how to fix it") instead.
- Return every node as node_ref(g, node, ...), so it has both an id and a label.
- Keep the output under 8 KB: respect top_k.
- Be deterministic: same input, same output. Randomised algorithms take a `seed` parameter (default 0).
"""
"""Check whether one node can reach another node in a graph."""

"""Check whether one node can reach another node in a graph."""

from graphkit.contract import check_node, error, get_graph, node_ref, ok


def run(store, graph_id, source=None, target=None, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err

    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}.")

    err = check_node(g, source, "source")
    if err:
        return err

    err = check_node(g, target, "target")
    if err:
        return err

    visited = set()
    stack = [source]

    while stack:
        current = stack.pop()

        if current in visited:
            continue

        visited.add(current)

        if current == target:
            result = {
                "source": node_ref(g, source),
                "target": node_ref(g, target),
                "reachable": True,
            }
            return ok(result, f"{target} is reachable from {source}.")

        if g.directed:
            neighbours = g.out_neighbors(current)
        else:
            neighbours = g.undirected_neighbors(current)

        for neighbour in neighbours:
            if neighbour not in visited:
                stack.append(neighbour)

    result = {
        "source": node_ref(g, source),
        "target": node_ref(g, target),
        "reachable": False,
    }

    return ok(result, f"{target} is not reachable from {source}.")

    # A tool that produces a node set or subgraph (marked with an arrow in the menu) registers it:
    #     sub_id = store.subgraph(graph_id, nodes, "Largest community of 'karate'")
    #     return ok(result, summary, result_graph_id=sub_id)
    # If it produces several node sets (e.g. communities), register each one, put its id in that
    # entry of the result as "graph_id", and return the largest one's id as result_graph_id.
