"""degree_distribution: histogram of node degrees, with summary statistics.

Degree is the number of edges at a node. For directed graphs `mode` picks in-degree, out-degree
or their sum (the NetworkX meaning of degree). Runs in O(V + E).
"""
import json
import math

from graphkit.contract import check_top_k, error, get_graph, node_ref, ok

MODES = ("total", "in", "out")
SIZE_BUDGET = 8000  # bytes of JSON; the contract limit is 8 KB (8192)
MAX_BINS = 40  # keeps the histogram well inside the 8 KB output limit on graphs with huge hubs


def _degree(g, node, mode):
    out_nbrs, in_nbrs = g.out_neighbors(node), g.in_neighbors(node)
    if not g.directed:
        # an undirected self-loop counts twice, as in NetworkX
        return len(out_nbrs) + (1 if node in out_nbrs else 0)
    if mode == "out":
        return len(out_nbrs)
    if mode == "in":
        return len(in_nbrs)
    return len(out_nbrs) + len(in_nbrs)


def _median(sorted_values):
    n = len(sorted_values)
    mid = n // 2
    return float(sorted_values[mid]) if n % 2 else (sorted_values[mid - 1] + sorted_values[mid]) / 2


def run(store, graph_id, mode="total", bin_width=1, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. degree_distribution takes "
                     f"graph_id, mode, bin_width and top_k.")
    if mode not in MODES:
        return error(f"mode must be one of {', '.join(MODES)}; got {mode!r}.")
    if not g.directed and mode != "total":
        return error(f"Graph '{graph_id}' is undirected, so it has no separate in- or out-degree. "
                     f"Use mode='total' (the default).")
    if isinstance(bin_width, bool) or not isinstance(bin_width, int) or bin_width < 1:
        return error(f"bin_width must be a whole number of at least 1; got {bin_width!r}.")
    k, err = check_top_k(top_k)
    if err:
        return err
    nodes = g.nodes()
    if not nodes:
        return error(f"Graph '{graph_id}' has no nodes, so there is no degree distribution.")

    degrees = {n: _degree(g, n, mode) for n in nodes}
    values = sorted(degrees.values())
    n_nodes, lo, hi = len(values), values[0], values[-1]
    mean = sum(values) / n_nodes

    width = bin_width
    if hi // width + 1 > MAX_BINS:
        width = math.ceil((hi + 1) / MAX_BINS)
    counts = {}
    for d in values:
        start = (d // width) * width
        counts[start] = counts.get(start, 0) + 1
    histogram = [{"degree": start, "degree_max": min(start + width - 1, hi), "count": c,
                  "fraction": round(c / n_nodes, 4)} for start, c in sorted(counts.items())]

    exact = {}
    for d in values:
        exact[d] = exact.get(d, 0) + 1
    common_degree = min(exact, key=lambda d: (-exact[d], d))
    median = _median(values)

    top = sorted(degrees.items(), key=lambda item: (-item[1], item[0]))[:k]
    result = {
        "mode": mode if g.directed else "total",
        "bin_width": width,
        "statistics": {"nodes": n_nodes, "min": lo, "max": hi, "mean": round(mean, 4), "median": median,
                       "most_common_degree": common_degree, "nodes_with_most_common_degree": exact[common_degree]},
        "histogram": histogram,
        "top_nodes": [node_ref(g, n, degree=d) for n, d in top],
    }
    what = "degrees"
    if g.directed:
        what = {"total": "total degrees (in + out)", "in": "in-degrees", "out": "out-degrees"}[mode]
    summary = (f"In '{graph_id}' the {n_nodes} nodes have {what} from {lo} to {hi} "
               f"(mean {mean:.2f}, median {median:g}); the most common degree is {common_degree} "
               f"({exact[common_degree]} nodes).")
    if width != bin_width:
        summary += f" Degrees are grouped in bins of {width} to keep the output small."
    out = ok(result, summary)
    # long labels can push top_k=100 past the 8 KB limit: drop the lowest-degree listed nodes until it fits
    while len(result["top_nodes"]) > 1 and len(json.dumps(out)) > SIZE_BUDGET:
        result["top_nodes"] = result["top_nodes"][:-1]
        out = ok(result, f"{summary} Only the top {len(result['top_nodes'])} nodes are listed "
                         f"to stay under the 8 KB output limit.")
    return out
