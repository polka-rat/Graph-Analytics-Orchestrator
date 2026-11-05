"""Top-k nodes by degree centrality (in and out on directed graphs)."""
from graphkit.contract import check_top_k, error, get_graph, node_ref, ok

MODES = ("total", "in", "out")


def _normalised(degree: int, n: int) -> float:
    if n <= 1:
        return 1.0
    return degree / (n - 1)


def run(store, graph_id, top_k=10, mode="total", **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. degree_centrality takes graph_id, top_k and mode.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if mode not in MODES:
        return error(f"mode must be one of {', '.join(MODES)}; got {mode!r}. Use total, in or out.")

    n = g.number_of_nodes()
    if n == 0:
        return ok([], "The graph has no nodes, so there is no degree centrality ranking.")

    rows = []
    for node in g.nodes():
        out_deg = len(g.out_neighbors(node))
        in_deg = len(g.in_neighbors(node))
        total_deg = out_deg + in_deg if g.directed else out_deg
        entry = {
            "node": node,
            "score": _normalised(total_deg, n),
            "in_score": _normalised(in_deg, n),
            "out_score": _normalised(out_deg, n),
        }
        rows.append(entry)

    if not g.directed or mode == "total":
        rank_key = "score"
    elif mode == "in":
        rank_key = "in_score"
    else:
        rank_key = "out_score"

    rows.sort(key=lambda item: (-item[rank_key], item["node"]))
    top = rows[:k]
    result = []
    for item in top:
        extra = {"score": round(item["score"], 6)}
        if g.directed:
            extra["in_score"] = round(item["in_score"], 6)
            extra["out_score"] = round(item["out_score"], 6)
        result.append(node_ref(g, item["node"], **extra))

    best = result[0]
    kind = "in-degree" if mode == "in" else "out-degree" if mode == "out" else "degree"
    summary = (
        f"{best['label']} has the highest {kind} centrality ({best[rank_key if rank_key != 'score' else 'score']}) "
        f"of {n} nodes."
    )
    if g.directed and mode == "total":
        summary = (
            f"{best['label']} has the highest degree centrality ({best['score']}) of {n} nodes "
            f"(in {best['in_score']}, out {best['out_score']})."
        )
    return ok(result, summary)
