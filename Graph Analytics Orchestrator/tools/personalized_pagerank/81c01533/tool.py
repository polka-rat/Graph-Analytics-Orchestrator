"""Computes Personalized PageRank (Random Walk with Restart) to find nodes most relevant to a seed node (non-negative edge weights only)

Rules (the validator checks them):
- Implement the algorithm yourself: standard library, NumPy and graphkit only.
- Get graphs only from the store; never open files, print, or use the network.
- Never crash: return error("what went wrong and how to fix it") instead.
- Return every node as node_ref(g, node, ...), so it has both an id and a label.
- Keep the output under 8 KB: respect top_k.
- Be deterministic: same input, same output. Randomised algorithms take a `seed` parameter (default 0).
"""
import math

from graphkit.contract import check_node, check_top_k, error, get_graph, node_ref, ok

MAX_ITER_LIMIT = 1000


def run(store, graph_id=None,seed_node=None,top_k=10,alpha=0.85, max_iter = 100,tol = 1e-5, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}.")
    if seed_node is None:
            return error(f"Seed node not specified.")
    
    err = check_node(g,seed_node, "seed_node")
    if err:
        return err
    k, err = check_top_k(top_k)
    if err:
        return err
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float)) or not (0.0 <= alpha < 1.0):
        return error("alpha must be a number in [0, 1), e.g. 0.85 (probability of continuing the walk).")
    if isinstance(max_iter, bool) or not isinstance(max_iter, int) or not 1 <= max_iter <= MAX_ITER_LIMIT:
        return error(f"max_iter must be an integer from 1 to {MAX_ITER_LIMIT}, e.g. 100.")
    if isinstance(tol, bool) or not isinstance(tol, (int, float)) or not math.isfinite(tol) or tol <= 0:
        return error("tol must be a positive finite number, e.g. 1e-6.")
    nodes = g.nodes()
    for node in nodes:
        if any(w < 0 for w in g.out_neighbors(node).values()):
            return error("Graph has negative edge weights; personalized_pagerank only supports non-negative weights.")

    scores = {node: 0.0 for node in nodes}
    scores[seed_node] = 1.0

    for _ in range(max_iter):
       
        new_scores = {node: 0.0 for node in nodes}
        
        for node in nodes:
          
            neighbors_dict = g.out_neighbors(node)
            
            total_weight = sum(neighbors_dict.values()) if neighbors_dict else 0
            if total_weight > 0:
                
                for neighbor, weight in neighbors_dict.items():
                    share = (scores[node] * alpha) * (weight / total_weight)
                    new_scores[neighbor] += share
        
            else:
              
                new_scores[seed_node] += scores[node] * alpha
                
       
        new_scores[seed_node] += (1.0 - alpha)

        diff = sum(abs(new_scores[n] - scores[n]) for n in nodes)
        scores = new_scores
        
        if diff < tol:
            break
   
    # ties (same score as shown in the output) are broken by node id, ascending
    sorted_nodes = sorted(nodes, key=lambda n: (-round(scores[n], 4), n))
    top_results = sorted_nodes[:k]
    items = [node_ref(g, n, score=round(scores[n], 4)) for n in top_results]
    return ok(
        result={"top_items": items},
        summary=f"Top 3 nodes most relevant to {g.label(seed_node)} ({seed_node}): "
                + ", ".join(f"{g.label(n)} ({scores[n]:.4f})" for n in top_results[:3]) + ".",
    )