"""Computes the Jaccard similarity score and shared neighbor count between two nodes.

Rules (the validator checks them):
- Implement the algorithm yourself: standard library, NumPy and graphkit only.
- Get graphs only from the store; never open files, print, or use the network.
- Never crash: return error("what went wrong and how to fix it") instead.
- Return every node as node_ref(g, node, ...), so it has both an id and a label.
- Keep the output under 8 KB: respect top_k.
- Be deterministic: same input, same output. Randomised algorithms take a `seed` parameter (default 0).
"""
from graphkit.contract import check_node, check_top_k, error, get_graph, node_ref, ok


def run(store, graph_id: str = None, node1: str = None, node2: str = None, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}.")
    if node1 is None or node2 is None:
        return error("Both node1 and node2 are required. Use lookup_node to find node ids.")
    err = check_node(g, node1, "node1")
    if err:
        return err
    err = check_node(g, node2, "node2")
    if err:
            return err
    #node_similarity tool:
    #needs 2 inputs for nodes to calculate similarity of 
    #use jaccard score get out_neighbours of both nodes and get the intersection ( for directed)
    # for undirected graph get all edges for each node and calculate jaccard score 
    #edge cases : check if AUB is 0 (prevent div with 0 ) set to 0.
    # if alice == bob then return 1 immediately 
    if g.directed:
         neighbours1 = set(g.out_neighbors(node1).keys())
         neighbours2 = set(g.out_neighbors(node2).keys())
    else:
        neighbours1 = set(g.out_neighbors(node1).keys())
        neighbours2 = set(g.out_neighbors(node2).keys())
    # a self-loop doesn't make a node its own common neighbour (same as networkx)
    intersection = (neighbours1 & neighbours2) - {node1, node2}
    union = neighbours1 | neighbours2
    jaccard_score=None
    if node1==node2:
         jaccard_score = 1.0 
    elif len(union) == 0:
         jaccard_score = 0.0
    else:
         jaccard_score = len(intersection)/len(union)
    jaccard_score = round(jaccard_score, 6)
    return ok(result = {'common_neighbours':len(intersection),'jaccard_score':jaccard_score},summary = f'{g.label(node1)} and {g.label(node2)} have {len(intersection)} common neighbours and a Jaccard similarity score of {jaccard_score}.')


        
