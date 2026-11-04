"""Extract the one-hop ego network centered on a specified node."""


"""TODO: one line saying what this tool computes.

Rules (the validator checks them):
- Implement the algorithm yourself: standard library, NumPy and graphkit only.
- Get graphs only from the store; never open files, print, or use the network.
- Never crash: return error("what went wrong and how to fix it") instead.
- Return every node as node_ref(g, node, ...), so it has both an id and a label.
- Keep the output under 8 KB: respect top_k.
- Be deterministic: same input, same output. Randomised algorithms take a `seed` parameter (default 0).
"""
from graphkit.contract import check_node, check_top_k, error, get_graph, node_ref, ok
# from graphkit.graph import undirected_neighbors
# from graphkit.store import subgraph

def run(store, graph_id:str, node:str = None, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}.")
    # if err:
    #     return err
    
    err = check_node(g,node)
    if err:
        return err
    
    neighbours = set(g.undirected_neighbors(node))
    
    ego_nodes = neighbours | {node}
    
    selected_nodes = sorted(ego_nodes)
    
    sub_id = store.subgraph(graph_id,selected_nodes,f"One-hop ego network centered on {g.label(node)} ({node})")
  
    result = {
        "ego": node_ref(g, node),
        "neighbors": [
            node_ref(g, n) for n in selected_nodes if n != node
        ],
        "nodes": [
            node_ref(g, n) for n in selected_nodes
        ],
        "number_of_nodes": len(selected_nodes),
        "number_of_edges": store.get(sub_id).number_of_edges(),
    }
    
    summary = (
        f"The ego network centered on {g.label(node)} ({node}) "
        f"contains {len(selected_nodes)} nodes and "
        f"{store.get(sub_id).number_of_edges()} edges."
    )

    return ok(result, summary, result_graph_id=sub_id)
     
    # TODO: your algorithm. Useful Graph methods:
    #   g.nodes(), g.number_of_nodes(), g.number_of_edges(), g.directed, g.weighted
    #   g.out_neighbors(n), g.in_neighbors(n), g.undirected_neighbors(n)   -> {neighbour: weight}
    #   g.edges() -> (u, v, weight), g.weight(u, v), g.label(n), g.node_attrs(n)
    # scores = {n: 0.0 for n in g.nodes()}

    # Sort by score, breaking ties by node id so the output is deterministic.
    # top = sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:k]
    # result = [node_ref(g, n, score=round(s, 6)) for n, s in top]
    # best = result[0]
    # summary = f"{best['label']} has the highest score ({best['score']}) of {g.number_of_nodes()} nodes."
    # return ok(result, summary)

    # A tool that produces a node set or subgraph (marked with an arrow in the menu) registers it:
    #     sub_id = store.subgraph(graph_id, nodes, "Largest community of 'karate'")
    #     return ok(result, summary, result_graph_id=sub_id)
    # If it produces several node sets (e.g. communities), register each one, put its id in that
    # entry of the result as "graph_id", and return the largest one's id as result_graph_id.
