"""degree_distribution: histogram of node degrees (in, out or total) with summary statistics."""
from graphkit.contract import error, get_graph, node_ref, ok

MODES = ("total", "in", "out")
MAX_BINS_LIMIT = 100


def _degree(g, node, mode):
    if not g.directed:
        return len(g.out_neighbors(node))
    if mode == "in":
        return len(g.in_neighbors(node))
    if mode == "out":
        return len(g.out_neighbors(node))
    return len(g.in_neighbors(node)) + len(g.out_neighbors(node))


def _median(sorted_values):
    n = len(sorted_values)
    mid = n // 2
    if n % 2:
        return float(sorted_values[mid])
    return (sorted_values[mid - 1] + sorted_values[mid]) / 2.0


def run(store, graph_id, mode="total", max_bins=20, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     f"degree_distribution takes graph_id, mode and max_bins.")
    if isinstance(max_bins, float) and max_bins.is_integer():
        max_bins = int(max_bins)   # an LLM may send 10.0 for an integer
    if mode not in MODES:
        return error(f"mode must be one of {', '.join(MODES)}; got {mode!r}.")
    if isinstance(max_bins, bool) or not isinstance(max_bins, int) or not 1 <= max_bins <= MAX_BINS_LIMIT:
        return error(f"max_bins must be a whole number from 1 to {MAX_BINS_LIMIT}; got {max_bins!r}.")

    nodes = g.nodes()
    n = len(nodes)
    if n == 0:
        return error(f"Graph '{graph_id}' has no nodes, so it has no degree distribution.")

    degrees = {v: _degree(g, v, mode) for v in nodes}
    values = sorted(degrees.values())
    counts = {}
    for d in values:
        counts[d] = counts.get(d, 0) + 1

    lo, hi = values[0], values[-1]
    span = hi - lo + 1
    width = 1 if span <= max_bins else -(-span // max_bins)

    bins = []
    start = lo
    while start <= hi:
        end = min(start + width - 1, hi)
        count = sum(c for d, c in counts.items() if start <= d <= end)
        if count:
            bins.append({"low": start, "high": end, "count": count, "fraction": round(count / n, 6)})
        start = end + 1

    mean = sum(values) / n
    most_common = min(counts, key=lambda d: (-counts[d], d))
    top = sorted(degrees.items(), key=lambda item: (-item[1], item[0]))[:5]
    top_nodes = [node_ref(g, v, degree=d) for v, d in top]

    result = {
        "mode": mode if g.directed else "undirected",
        "num_nodes": n,
        "min_degree": lo,
        "max_degree": hi,
        "mean_degree": round(mean, 6),
        "median_degree": round(_median(values), 6),
        "most_common_degree": most_common,
        "isolated_nodes": counts.get(0, 0),
        "bin_width": width,
        "histogram": bins,
        "highest_degree_nodes": top_nodes,
    }

    kind = f"{mode} degree" if g.directed else "degree"
    summary = (f"In '{graph_id}' ({n} nodes) the {kind} ranges from {lo} to {hi} with mean {round(mean, 2)} "
               f"and median {round(_median(values), 2)}; the most common value is {most_common} "
               f"({counts[most_common]} nodes). The highest is {top_nodes[0]['label']} with {top_nodes[0]['degree']}.")
    return ok(result, summary)
