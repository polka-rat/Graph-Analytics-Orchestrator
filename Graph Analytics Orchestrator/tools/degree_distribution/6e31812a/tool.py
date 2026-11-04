"""Histogram of node degrees (how many nodes have each number of connections), with summary statistics.

Algorithm: one pass over the nodes to compute each node's degree from the adjacency maps,
then a count of how many nodes have each degree. Time O(V + E), memory O(V).

Degree conventions (the same as NetworkX, so results can be checked against nx.degree_histogram):
- undirected graph: degree = number of neighbours; a self-loop counts twice;
- directed graph:   mode="total" -> in-degree + out-degree (default), "in" -> in-degree, "out" -> out-degree.
"""
import json
import math
import statistics
from collections import Counter

from graphkit.contract import MAX_OUTPUT_BYTES, error, get_graph, ok

MODES = ("total", "in", "out")
MAX_BINS = 100
AUTO_BINS = 50          # used only if the exact histogram would not fit in the 8 KB output limit
SIZE_MARGIN = 300       # bytes kept free for the summary sentence


def _degrees(g, mode):
    """{node: degree} under the chosen mode."""
    degrees = {}
    for n in g.nodes():
        if g.directed:
            out_d, in_d = len(g.out_neighbors(n)), len(g.in_neighbors(n))
            degrees[n] = {"total": out_d + in_d, "in": in_d, "out": out_d}[mode]
        else:
            nbrs = g.out_neighbors(n)
            degrees[n] = len(nbrs) + (1 if n in nbrs else 0)  # self-loop counts twice
    return degrees


def _exact_histogram(counts):
    """One row per degree that occurs, in increasing degree order."""
    return [{"degree": d, "count": c} for d, c in sorted(counts.items())]


def _binned_histogram(counts, lo, hi, bins):
    """`bins` equal-width ranges of whole degrees covering lo..hi (empty ranges included)."""
    width = max(1, math.ceil((hi - lo + 1) / bins))
    rows = []
    start = lo
    while start <= hi:
        end = min(start + width - 1, hi)
        rows.append({"degree_min": start, "degree_max": end,
                     "count": sum(c for d, c in counts.items() if start <= d <= end)})
        start = end + 1
    return rows


def _size(obj):
    return len(json.dumps(obj, allow_nan=False, sort_keys=True).encode("utf-8"))


def run(store, graph_id, mode="total", bins=None, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     f"degree_distribution takes graph_id, mode and bins.")
    if mode not in MODES:
        return error(f"mode must be one of {', '.join(MODES)}; got {mode!r}. "
                     f"Use 'total' for all connections, 'in' or 'out' for directed graphs.")
    if not g.directed and mode != "total":
        return error(f"Graph '{graph_id}' is undirected, so in- and out-degree are just the degree. "
                     f"Call again with mode='total' (the default).")
    if bins is not None and (isinstance(bins, bool) or not isinstance(bins, int) or not 1 <= bins <= MAX_BINS):
        return error(f"bins must be a whole number from 1 to {MAX_BINS}, or left out for the exact "
                     f"histogram; got {bins!r}.")
    n = g.number_of_nodes()
    if n == 0:
        return error(f"Graph '{graph_id}' has no nodes, so it has no degree distribution. "
                     f"Use list_graphs to pick a non-empty graph.")

    degrees = _degrees(g, mode)
    values = list(degrees.values())
    counts = Counter(values)
    lo, hi = min(values), max(values)
    mean = sum(values) / n
    median = statistics.median(values)
    mode_degree, mode_count = min(counts.items(), key=lambda dc: (-dc[1], dc[0]))  # ties -> smaller degree
    below_mean = sum(1 for v in values if v < mean) / n

    result = {
        "graph_id": graph_id,
        "directed": g.directed,
        "mode": mode,
        "nodes": n,
        "edges": g.number_of_edges(),
        "min_degree": lo,
        "max_degree": hi,
        "mean_degree": round(mean, 6),
        "median_degree": round(float(median), 6),
        "most_common_degree": {"degree": mode_degree, "count": mode_count},
        "isolated_nodes": counts.get(0, 0),
        "share_below_mean": round(below_mean, 6),
        "binned": False,
        "histogram": _exact_histogram(counts),
    }
    if bins is not None or _size(result) > MAX_OUTPUT_BYTES - SIZE_MARGIN:
        result["binned"] = True
        result["histogram"] = _binned_histogram(counts, lo, hi, bins or AUTO_BINS)

    kind = {"total": "degree", "in": "in-degree", "out": "out-degree"}[mode]
    if g.directed and mode == "total":
        kind = "total (in + out) degree"
    if mean > 1.25 * median:
        shape = "right-skewed: most nodes have few connections while a few hubs have many"
    elif mean < 0.8 * median:
        shape = "left-skewed: most nodes have more connections than a few weakly connected ones"
    else:
        shape = "fairly balanced around the mean"
    summary = (f"In '{graph_id}' ({n} nodes), {kind} ranges from {lo} to {hi} with median {result['median_degree']:g} "
               f"and mean {mean:.2f}; the most common value is {mode_degree} ({mode_count} nodes). "
               f"{below_mean:.0%} of nodes are below the mean, so the distribution is {shape}.")
    return ok(result, summary)
