"""maximal_cliques: enumerate maximal cliques with Bron-Kerbosch (pivoting).

Rules (the validator checks them):
- Implement the algorithm yourself: standard library, NumPy and graphkit only.
- Get graphs only from the store; never open files, print, or use the network.
- Never crash: return error("what went wrong and how to fix it") instead.
- Return every node as node_ref(g, node, ...), so it has both an id and a label.
- Keep the output under 8 KB: respect top_k.
- Be deterministic: same input, same output.
"""
import json

from graphkit.contract import (
    MAX_OUTPUT_BYTES,
    check_top_k,
    error,
    get_graph,
    node_ref,
    ok,
)

# Each recursive call adds one node to the clique, so the depth is bounded by the size of
# the largest clique. This headroom is far beyond anything the datasets produce.
RECURSION_HEADROOM = 10000


def _neighbourhoods(g):
    """Undirected adjacency sets. A clique is an undirected notion, so edge direction is
    ignored: u and v are adjacent if an edge runs either way between them. Self-loops are
    dropped, since a node is not its own neighbour."""
    adjacency = {}
    for v in g.nodes():
        neighbours = set(g.undirected_neighbors(v))
        neighbours.discard(v)
        adjacency[v] = neighbours
    return adjacency


def _bron_kerbosch(adjacency):
    """Every maximal clique, by Bron-Kerbosch with pivoting.

    R is the clique built so far, P the candidates that could still extend it, and X the
    nodes already explored (which stops the same clique being reported twice). When P and
    X are both empty, R cannot be extended, so it is maximal.

    Pivoting is what makes this tractable: any maximal clique either excludes the pivot u
    or contains one of u's non-neighbours, so branching over P - N(u) rather than all of P
    skips work that could not produce a new clique. The pivot is chosen to maximise
    |P and N(u)|, with the node id as a tie-break so the search is reproducible.
    """
    cliques = []
    stack = [(set(), set(adjacency), set())]
    while stack:
        clique, candidates, explored = stack.pop()
        if not candidates and not explored:
            cliques.append(clique)
            continue
        pivot = max(candidates | explored,
                    key=lambda u: (len(candidates & adjacency[u]), u))
        # Copies, because the branch loop below mutates them as it walks the candidates.
        candidates = set(candidates)
        explored = set(explored)
        for v in sorted(candidates - adjacency[pivot]):
            stack.append((clique | {v},
                          candidates & adjacency[v],
                          explored & adjacency[v]))
            candidates.discard(v)
            explored.add(v)
    return cliques


def run(store, graph_id, top_k=10, min_size=1, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(
            f"Unknown parameter(s): {', '.join(sorted(params))}. "
            f"maximal_cliques takes graph_id, top_k and min_size."
        )
    k, err = check_top_k(top_k)
    if err:
        return err
    if isinstance(min_size, bool) or not isinstance(min_size, int) or min_size < 1:
        return error(f"min_size must be a whole number of 1 or more; got {min_size!r}.")

    if g.number_of_nodes() == 0:
        return error(
            f"Graph '{g.graph_id}' has no nodes, so it contains no cliques. "
            f"Use list_graphs to see the available graphs."
        )

    adjacency = _neighbourhoods(g)
    cliques = [c for c in _bron_kerbosch(adjacency) if len(c) >= min_size]

    if not cliques:
        largest_possible = max((len(c) for c in _bron_kerbosch(adjacency)), default=0)
        return error(
            f"Graph '{g.graph_id}' has no maximal clique with at least {min_size} nodes; "
            f"the largest one has {largest_possible}. Lower min_size and try again."
        )

    # Biggest first, then by node ids ascending, so the ranking is fully deterministic.
    ranked = sorted((sorted(c) for c in cliques), key=lambda c: (-len(c), c))
    total = len(ranked)
    largest_size = len(ranked[0])

    def entries_for(chosen, ids):
        return [
            {"graph_id": gid, "size": len(c), "nodes": [node_ref(g, v) for v in c]}
            for c, gid in zip(chosen, ids)
        ]

    def summarise(shown, nodes_shown):
        best = ranked[0]
        names = ", ".join(g.label(v) for v in best[:5])
        if largest_size > 5:
            names += f" and {largest_size - 5} more"
        text = (
            f"The largest group in '{g.graph_id}' where every member is connected to every "
            f"other has {largest_size} members: {names}. "
            f"{total:,} maximal cliques were found in all"
        )
        text += f"; showing the {shown} largest." if shown < total else "."
        if nodes_shown is not None:
            text += (
                f" Only the first {nodes_shown} members of each clique are listed, to stay "
                f"within the 8 KB response limit."
            )
        return text

    def size_of(payload):
        return len(json.dumps(payload, allow_nan=False, sort_keys=True).encode("utf-8"))

    # Work out how many cliques fit in the 8 KB budget before registering any subgraph, so
    # the store is not littered with ids that never reach the caller. A placeholder id that
    # is longer than any real one keeps the estimate conservative.
    root = g.graph_id.split("~")[0]
    placeholder = f"{root}~999999"
    chosen = ranked[:k]
    while len(chosen) > 1:
        probe = ok(entries_for(chosen, [placeholder] * len(chosen)),
                   summarise(len(chosen), None), placeholder)
        if size_of(probe) <= MAX_OUTPUT_BYTES:
            break
        chosen = chosen[:-1]

    # A single clique large enough to overflow on its own: list as many members as fit.
    nodes_shown = None
    probe = ok(entries_for(chosen, [placeholder] * len(chosen)), summarise(len(chosen), None), placeholder)
    if size_of(probe) > MAX_OUTPUT_BYTES:
        limit = len(chosen[0])
        while limit > 1:
            limit -= 1
            trimmed = [c[:limit] for c in chosen]
            probe = ok(entries_for(trimmed, [placeholder] * len(trimmed)),
                       summarise(len(chosen), limit), placeholder)
            if size_of(probe) <= MAX_OUTPUT_BYTES:
                break
        nodes_shown = limit

    # Register each returned clique as a subgraph so another tool can run on it next; the
    # largest one's id is the result_graph_id.
    ids = []
    for clique in chosen:
        ids.append(store.subgraph(
            graph_id,
            clique,
            f"Maximal clique of {len(clique)} nodes in '{g.graph_id}'",
        ))

    listed = [c if nodes_shown is None else c[:nodes_shown] for c in chosen]
    result = entries_for(listed, ids)
    for entry, clique in zip(result, chosen):
        entry["size"] = len(clique)
    return ok(result, summarise(len(chosen), nodes_shown), ids[0])
