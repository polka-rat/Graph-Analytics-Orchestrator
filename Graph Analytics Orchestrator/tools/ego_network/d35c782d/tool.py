"""Ego network of a node: the node (ego), its neighbours (alters) and the edges around them.

Rules (the validator checks them):
- Implement the algorithm yourself: standard library, NumPy and graphkit only.
- Get graphs only from the store; never open files, print, or use the network.
- Never crash: return error("what went wrong and how to fix it") instead.
- Return every node as node_ref(g, node, ...), so it has both an id and a label.
- Keep the output under 8 KB: respect top_k.
- Be deterministic: same input, same output. Randomised algorithms take a `seed` parameter (default 0).
"""
import json

from graphkit.contract import MAX_OUTPUT_BYTES, check_node, check_top_k, error, get_graph, node_ref, ok

LEVELS = (1.0, 1.5, 2.0)
DIRECTIONS = ("out", "in", "both")


def _neighbour_getter(g, direction):
    """Which neighbours count as 'connected to' a node: leaving it, arriving at it, or either."""
    if direction == "out":
        return g.out_neighbors
    if direction == "in":
        return g.in_neighbors
    return g.undirected_neighbors


def _alter_density(g, alters):
    """Edges among the alters divided by the edges that could exist among them (None if fewer than 2)."""
    k = len(alters)
    if k < 2:
        return None
    members = set(alters)
    m = sum(1 for a in alters for b in g.out_neighbors(a) if b in members and b != a)
    if g.directed:
        return round(m / (k * (k - 1)), 6)
    return round((m // 2) / (k * (k - 1) // 2), 6)  # each undirected edge was counted from both ends


def _alter_component_sizes(g, alters):
    """Sizes (largest first) of the connected groups the alters form among themselves, direction ignored."""
    members = set(alters)
    seen = set()
    sizes = []
    for start in sorted(alters):
        if start in seen:
            continue
        seen.add(start)
        stack, size = [start], 0
        while stack:
            u = stack.pop()
            size += 1
            for v in g.undirected_neighbors(u):
                if v in members and v not in seen:
                    seen.add(v)
                    stack.append(v)
        sizes.append(size)
    return sorted(sizes, reverse=True)


def run(store, graph_id, node=None, level=1.5, direction="out", include_ego=True, alter_density=False,
        top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}.")
    if node is None:
        return error("Give the id of the ego node in 'node', e.g. node='MAA'. Use lookup_node to find node ids.")
    err = check_node(g, node)
    if err:
        return err
    k, err = check_top_k(top_k)
    if err:
        return err
    if isinstance(level, bool) or level not in LEVELS:
        return error(f"level must be 1.0 (ego and its direct links), 1.5 (adds links among neighbours) "
                     f"or 2.0 (adds neighbours of neighbours); got {level!r}.")
    level = float(level)
    if direction not in DIRECTIONS:
        return error(f"direction must be one of {', '.join(DIRECTIONS)}; got {direction!r}.")
    if not isinstance(include_ego, bool) or not isinstance(alter_density, bool):
        return error("include_ego and alter_density must be true or false.")
    if level == 1.0 and not include_ego:
        return error("Level 1.0 without the ego has no edges. Use level 1.5 or 2.0 with include_ego=false.")

    # Step 1: find the alters (direct neighbours) and, for level 2.0, the neighbours of the alters.
    nbrs = _neighbour_getter(g, direction)
    alters = sorted(set(nbrs(node)) - {node})
    if not alters and not include_ego:
        return error(f"'{node}' has no neighbours, so its ego network without the ego is empty. "
                     f"Use include_ego=true.")
    distance = {node: 0}
    for a in alters:
        distance[a] = 1
    if level == 2.0:
        for a in alters:
            for b in nbrs(a):
                if b not in distance:
                    distance[b] = 2

    # Step 2: register the subgraph (level 1.0 keeps only the ego-alter edges, the others keep every edge among the nodes).
    description = f"Ego network of '{node}' in '{graph_id}' (level {level}, direction {direction})"
    if level == 1.0:
        edges = []
        for a in alters:
            if g.has_edge(node, a) and (direction != "in" or not g.directed):
                edges.append((node, a))
            if g.directed and direction != "out" and g.has_edge(a, node):
                edges.append((a, node))
        if edges:
            sub_id = store.edge_subgraph(graph_id, edges, description)
        else:
            sub_id = store.subgraph(graph_id, [node], description)
    else:
        members = [n for n in distance if include_ego or n != node]
        sub_id = store.subgraph(graph_id, members, description)
    sub = store.get(sub_id)

    # Step 3: list the nodes, nearest first and, within a distance, by node id (ties by id).
    ordered = sorted(sub.nodes(), key=lambda n: (distance[n], n))

    # Step 4: optional extras: alter density, and the broker check when the ego is left out.
    extra, notes = {}, []
    if alter_density:
        density = _alter_density(g, alters)
        extra["alter_density"] = density
        notes.append(f"Alter density is {density}." if density is not None
                     else "Alter density is undefined with fewer than 2 neighbours.")
    if not include_ego:
        sizes = _alter_component_sizes(g, alters)
        extra["alter_components"] = {"count": len(sizes), "largest_sizes": sizes[:5]}
        if len(sizes) > 1:
            notes.append(f"Without the ego, its {len(alters)} neighbours fall into {len(sizes)} separate groups, "
                         f"so the ego links groups that are otherwise unconnected.")
        else:
            notes.append(f"Without the ego, its {len(alters)} neighbour(s) stay in one connected group, "
                         f"so the ego is not a bridge.")

    # Step 5: build the output, listing fewer nodes if it would be over the 8 KB limit.
    ego = g.label(node)
    way = f", following {direction} edges" if g.directed else ""

    def build(shown):
        listed = [node_ref(g, n, distance=distance[n]) for n in ordered[:shown]]
        summary = (f"Ego network of {ego} ({node}), level {level}{way}: {sub.number_of_nodes()} nodes and "
                   f"{sub.number_of_edges()} edges, {len(alters)} direct neighbours; showing {len(listed)} nodes. "
                   + " ".join(notes)).strip()
        result = {"ego": node_ref(g, node), "level": level, "n_nodes": sub.number_of_nodes(),
                  "n_edges": sub.number_of_edges(), "n_neighbors": len(alters), "nodes": listed, **extra}
        return ok(result, summary, result_graph_id=sub_id)

    shown = min(k, len(ordered))
    out = build(shown)
    while shown > 1 and len(json.dumps(out, sort_keys=True).encode("utf-8")) > MAX_OUTPUT_BYTES - 500:
        shown -= 1
        out = build(shown)
    return out