"""Directed or undirected reachability using breadth-first search."""
from collections import deque
import json
from graphkit.contract import check_node, error, get_graph, node_ref, ok


def run(store, graph_id=None, source=None, target=None, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. Use source and target node IDs.")
    for name, node in (("source", source), ("target", target)):
        err = check_node(g, node, name)
        if err:
            return err
    seen = {source}
    queue = deque([source])
    while queue and target not in seen:
        u = queue.popleft()
        for v in g.out_neighbors(u):
            if v not in seen:
                seen.add(v)
                queue.append(v)
    reachable = target in seen
    out = ok({"source": node_ref(g, source), "target": node_ref(g, target),
              "reachable": reachable},
             f"A path {'exists' if reachable else 'does not exist'} from {g.label(source)} to {g.label(target)}.")
    if len(json.dumps(out).encode()) > 8192:
        return error("Node labels exceed the response size limit; use a graph with shorter labels.")
    return out
