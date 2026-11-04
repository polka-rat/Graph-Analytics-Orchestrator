"""
Tool to compute the shortest path between two nodes in an unweighted graph. It uses a breadth-first search (BFS) algorithm to find the shortest path from the source node to the destination node. The tool returns the sequence of nodes in the shortest path and a summary of the path length.

Rules (the validator checks them):
- Implement the algorithm yourself: standard library, NumPy and graphkit only.
- Get graphs only from the store; never open files, print, or use the network.
- Never crash: return error("what went wrong and how to fix it") instead.
- Return every node as node_ref(g, node, ...), so it has both an id and a label.
- Keep the output under 8 KB: respect top_k.
- Be deterministic: same input, same output. Randomised algorithms take a `seed` parameter (default 0).
"""
from graphkit.contract import check_node, error, get_graph, node_ref, ok


def run(store, graph_id, src=None,dest=None, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if not src:
        return error("Missing required parameter: src.")
    err = check_node(g, src,"src")
    if err:
        return err
    if not dest:
        return error("Missing required parameter: dest.")
    err = check_node(g, dest,"dest")
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}.")
    
    parent={src:None}
    queue = [src]
    visited = [src]
    
    travel_seq =[]
    while queue:
        current=queue.pop(0)
        if current==dest:
            while parent[current]:
                travel_seq.append(current)
                current=parent[current]
                
            travel_seq.append(current)
            break
        
        for neighbor in g.out_neighbors(current):
            if neighbor not in visited:
                visited.append(neighbor)
                queue.append(neighbor)
                parent[neighbor]=current
    
    if not travel_seq:
        return error(f"No path found from '{src}' to '{dest}'.")
    
    travel_seq.reverse()
    result = [node_ref(g, n) for n in travel_seq]
    summary = f"Shortest path from '{src}' to '{dest}' is {len(travel_seq)-1} edges long."
    return ok(result, summary)

