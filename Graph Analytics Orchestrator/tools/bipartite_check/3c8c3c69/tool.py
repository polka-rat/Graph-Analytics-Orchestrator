import json
from collections import deque

from graphkit.contract import MAX_OUTPUT_BYTES, check_top_k, error, get_graph, node_ref, ok

OUTPUT_BUDGET = MAX_OUTPUT_BYTES - 256


def _two_colour(g):
    colour = {}
    parent = {}
    n_components = 0
    for start in g.nodes():
        if start in colour:
            continue
        if not g.undirected_neighbors(start):
            n_components += 1
            continue
        if g.directed and not g.out_neighbors(start):
            continue
        n_components += 1
        colour[start] = 1
        parent[start] = None
        queue = deque([start])
        while queue:
            u = queue.popleft()
            for v in g.undirected_neighbors(u):
                if v not in colour:
                    colour[v] = 1 - colour[u]
                    parent[v] = u
                    queue.append(v)
                elif colour[v] == colour[u]:
                    return None, None, _odd_cycle(u, v, parent)
    for n in g.nodes():
        if n not in colour:
            colour[n] = 0
    return colour, n_components, None


def _odd_cycle(u, v, parent):
    if u == v:
        return [u]
    left = [u]
    right = [v]
    a = u
    b = v
    while a != b:
        a = parent[a]
        b = parent[b]
        left.append(a)
        right.append(b)
    right.pop()
    right.reverse()
    return left + right


def _matching_attribute(g, side_a, side_b):
    if not side_a or not side_b:
        return None
    for attr, value in g.node_attrs(side_a[0]).items():
        if attr == "label" or not isinstance(value, str):
            continue
        values_a = set()
        for n in side_a:
            values_a.add(g.node_attrs(n).get(attr))
        values_b = set()
        for n in side_b:
            values_b.add(g.node_attrs(n).get(attr))
        if len(values_a) == 1 and len(values_b) == 1 and values_a != values_b:
            return attr, values_a.pop(), values_b.pop()
    return None


def _size(out):
    return len(json.dumps(out, sort_keys=True).encode("utf-8"))


def run(store, graph_id, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. bipartite_check takes graph_id and top_k.")
    top_k, err = check_top_k(top_k)
    if err:
        return err
    if g.number_of_nodes() == 0:
        return error(f"Graph '{graph_id}' has no nodes, so there is nothing to split. "
                     f"Use list_graphs to pick another graph.")

    if g.directed:
        note = " Edge direction is ignored."
    else:
        note = ""
    colour, n_components, cycle = _two_colour(g)

    if cycle is not None:
        edges = []
        if len(cycle) == 1:
            edges.append((cycle[0], cycle[0]))
        else:
            for i in range(len(cycle)):
                a = cycle[i]
                b = cycle[(i + 1) % len(cycle)]
                if g.has_edge(a, b):
                    edges.append((a, b))
                else:
                    edges.append((b, a))
        sub_id = store.edge_subgraph(graph_id, edges, f"An odd cycle in '{graph_id}' (proof it is not bipartite)")
        names = []
        for n in cycle + [cycle[0]]:
            names.append(f"{g.label(n)} ({n})")
        path = " - ".join(names)
        result = {"is_bipartite": False, "odd_cycle_length": len(cycle),
                  "odd_cycle": [node_ref(g, n) for n in cycle]}
        summary = (f"'{graph_id}' is not bipartite: it contains a cycle of odd length {len(cycle)} "
                   f"({path}), and an odd cycle cannot be split into two sides.{note}")
        if _size(ok(result, summary)) > OUTPUT_BUDGET:
            result["odd_cycle"] = result["odd_cycle"][:top_k]
            summary = (f"'{graph_id}' is not bipartite: it contains a cycle of odd length {len(cycle)} "
                       f"(registered as subgraph '{sub_id}'), and an odd cycle cannot be split into two sides.{note}")
        return ok(result, summary, result_graph_id=sub_id)

    side_a = []
    side_b = []
    for n in g.nodes():
        if colour[n] == 1:
            side_a.append(n)
        else:
            side_b.append(n)
    side_a.sort()
    side_b.sort()
    id_a = store.subgraph(graph_id, side_a, f"Side A of the bipartite graph '{graph_id}'")
    id_b = store.subgraph(graph_id, side_b, f"Side B of the bipartite graph '{graph_id}'")
    if len(side_b) > len(side_a):
        largest = id_b
    else:
        largest = id_a
    match = _matching_attribute(g, side_a, side_b)

    text = f"'{graph_id}' is bipartite: every edge joins side A ({len(side_a)} nodes) to side B ({len(side_b)} nodes)."
    if match:
        text += f" Side A is exactly the nodes with {match[0]}='{match[1]}', side B those with {match[0]}='{match[2]}'."
    if n_components > 1:
        text += (f" The graph has {n_components} separate parts, so the split is not unique: "
                 f"each part's sides can be swapped.")
    text += note

    bigger = max(len(side_a), len(side_b))
    shown = min(top_k, bigger)
    while True:
        sides = [{"side": "A", "size": len(side_a), "graph_id": id_a, "nodes": [node_ref(g, n) for n in side_a[:shown]]},
                 {"side": "B", "size": len(side_b), "graph_id": id_b, "nodes": [node_ref(g, n) for n in side_b[:shown]]}]
        result = {"is_bipartite": True, "components": n_components, "sides": sides}
        if match:
            result["sides_match_attribute"] = {"attribute": match[0], "A": match[1], "B": match[2]}
        if shown < bigger:
            listing = f" Each side lists up to {shown} nodes (by id); subgraphs '{id_a}' and '{id_b}' hold them all."
        else:
            listing = f" The sides are subgraphs '{id_a}' and '{id_b}'."
        out = ok(result, text + listing, result_graph_id=largest)
        if _size(out) <= OUTPUT_BUDGET or shown == 0:
            return out
        shown -= 1
