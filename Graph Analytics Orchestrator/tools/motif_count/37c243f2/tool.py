"""Count triangle and feed-forward-loop motifs in a graph."""

from itertools import combinations

from graphkit.contract import error, get_graph, ok


def run(store, graph_id: str, top_k: int = 15, **params) -> dict:
    if params:
        return error(f"Unknown parameter(s): {', '.join(sorted(params))}.")

    g, err = get_graph(store, graph_id)
    if err:
        return err

    if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= 100:
        return error("top_k must be a whole number from 1 to 100.")

    nodes = sorted(g.nodes())
    motifs = []

    if not g.directed:
        neighbors = {node: set(g.neighbors(node)) for node in nodes}

        # Each undirected triangle is counted once.
        for a, b, c in combinations(nodes, 3):
            if b in neighbors[a] and c in neighbors[a] and c in neighbors[b]:
                motifs.append({
                    "type": "triangle",
                    "nodes": [a, b, c],
                })

        motif_type = "triangle"
    else:
        outgoing = {node: set(g.out_neighbors(node)) for node in nodes}

        # A feed-forward loop is A->B, A->C, B->C.
        for a in nodes:
            for b in sorted(outgoing[a]):
                if b == a:
                    continue
                for c in sorted(outgoing[a] & outgoing[b]):
                    if c != a and c != b:
                        motifs.append({
                            "type": "feed_forward_loop",
                            "nodes": [a, b, c],
                        })

        motif_type = "feed_forward_loop"

    total = len(motifs)
    examples = motifs[:top_k]

    result = {
        "motif_type": motif_type,
        "count": total,
        "top_k": top_k,
        "examples": examples,
    }

    summary = (
        f"Found {total} {motif_type.replace('_', ' ')} motif(s); "
        f"returning {len(examples)} example(s)."
    )

    return ok(result, summary)
