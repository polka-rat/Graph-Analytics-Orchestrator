"""graph_summary: size, density, degree statistics and connectivity of a whole graph."""
from graphkit.contract import error, get_graph, node_ref, ok


def _degrees(g):
    """Total degree of every node (in + out for directed graphs; a self-loop counts twice)."""
    deg = {}
    for v in g.nodes():
        if g.directed:
            deg[v] = len(g.out_neighbors(v)) + len(g.in_neighbors(v))
        else:
            nbrs = g.out_neighbors(v)
            deg[v] = len(nbrs) + (1 if v in nbrs else 0)
    return deg


def _components(g):
    """Sizes of the (weakly) connected components, ignoring edge direction."""
    seen = set()
    sizes = []
    for start in g.nodes():
        if start in seen:
            continue
        seen.add(start)
        stack = [start]
        size = 0
        while stack:
            u = stack.pop()
            size += 1
            for w in g.undirected_neighbors(u):
                if w not in seen:
                    seen.add(w)
                    stack.append(w)
        sizes.append(size)
    return sizes


def run(store, graph_id, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. graph_summary takes only graph_id.")

    n, m = g.number_of_nodes(), g.number_of_edges()
    if n == 0:
        return error(f"Graph '{graph_id}' has no nodes, so there is nothing to summarise. "
                     f"Use list_graphs to pick another graph.")

    deg = _degrees(g)
    possible = n * (n - 1) if g.directed else n * (n - 1) / 2
    density = m / possible if possible else 0.0
    ordered = sorted(deg.items(), key=lambda item: (-item[1], item[0]))
    top_node, top_deg = ordered[0]
    isolated = sum(1 for d in deg.values() if d == 0)
    self_loops = sum(1 for u, v, _ in g.edges() if u == v)
    sizes = _components(g)

    result = {
        "graph_id": graph_id,
        "directed": g.directed,
        "weighted": g.weighted,
        "nodes": n,
        "edges": m,
        "density": round(density, 6),
        "average_degree": round(2 * m / n, 6),
        "min_degree": min(deg.values()),
        "max_degree": top_deg,
        "highest_degree_node": node_ref(g, top_node, degree=top_deg),
        "isolated_nodes": isolated,
        "self_loops": self_loops,
        "connected_components": len(sizes),
        "largest_component_size": max(sizes),
    }
    if g.directed:
        result["average_out_degree"] = round(m / n, 6)
        result["average_in_degree"] = round(m / n, 6)
        reciprocal = sum(1 for u, v, _ in g.edges() if g.has_edge(v, u))
        result["reciprocity"] = round(reciprocal / m, 6) if m else 0.0
    if g.weighted and m:
        total = sum(w for _, _, w in g.edges())
        result["total_weight"] = round(total, 6)
        result["average_weight"] = round(total / m, 6)

    kind = ("directed" if g.directed else "undirected") + (" and weighted" if g.weighted else "")
    comp_word = "component" if len(sizes) == 1 else "components"
    summary = (f"Graph '{graph_id}' is {kind} with {n:,} nodes and {m:,} edges; density {result['density']}, "
               f"average degree {result['average_degree']}, {len(sizes)} connected {comp_word} "
               f"(largest has {max(sizes):,} nodes).")
    return ok(result, summary)
