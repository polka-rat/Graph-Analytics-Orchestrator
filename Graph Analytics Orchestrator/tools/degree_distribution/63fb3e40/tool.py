"""Degree distribution: a histogram of node degrees, with summary statistics.

Degree counts edges, not weights. For undirected graphs it is the number of incident edges
(a self-loop counts twice, as in NetworkX). For directed graphs `degree_type` picks the
total degree (in + out, as NetworkX's G.degree), the in-degree or the out-degree.
Runs in O(n + m) time.
"""
import math
import statistics

from graphkit.contract import error, get_graph, node_ref, ok

DEGREE_TYPES = ("total", "in", "out")
MAX_BINS = 200          # keeps the response well under the 8 KB limit
MAX_HUBS = 5            # highest-degree nodes listed in the result
MAX_BIN_WIDTH = 10_000


def _degrees(g, degree_type):
    """{node: degree} for the requested degree type."""
    if not g.directed:
        # out_neighbors == in_neighbors here; a self-loop adds 2, as in NetworkX.
        return {n: len(g.out_neighbors(n)) + (1 if g.has_edge(n, n) else 0) for n in g.nodes()}
    if degree_type == "in":
        return {n: len(g.in_neighbors(n)) for n in g.nodes()}
    if degree_type == "out":
        return {n: len(g.out_neighbors(n)) for n in g.nodes()}
    return {n: len(g.in_neighbors(n)) + len(g.out_neighbors(n)) for n in g.nodes()}


def _histogram(counts, max_degree, width):
    """Non-empty bins in increasing order of degree."""
    if width == 1:
        return [{"degree": d, "count": counts[d]} for d in sorted(counts)]
    bins = {}
    for d, c in counts.items():
        bins[d // width] = bins.get(d // width, 0) + c
    return [{"degree_from": b * width, "degree_to": min(b * width + width - 1, max_degree), "count": c}
            for b, c in sorted(bins.items())]


def run(store, graph_id, degree_type="total", bin_width=1, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     f"degree_distribution takes graph_id, degree_type and bin_width.")
    if degree_type not in DEGREE_TYPES:
        return error(f"degree_type must be one of {', '.join(DEGREE_TYPES)}; got {degree_type!r}.")
    if isinstance(bin_width, bool) or not isinstance(bin_width, int) or not 1 <= bin_width <= MAX_BIN_WIDTH:
        return error(f"bin_width must be a whole number from 1 to {MAX_BIN_WIDTH}; got {bin_width!r}.")
    n = g.number_of_nodes()
    if n == 0:
        return error(f"Graph '{graph_id}' has no nodes, so it has no degree distribution. "
                     f"Use list_graphs to pick another graph.")

    # For undirected graphs in- and out-degree are the same as the degree.
    kind = degree_type if g.directed else "total"
    deg = _degrees(g, kind)
    values = sorted(deg.values())

    counts = {}
    for d in values:
        counts[d] = counts.get(d, 0) + 1
    min_d, max_d = values[0], values[-1]
    mean = sum(values) / n
    median = statistics.median(values)
    std = statistics.pstdev(values)
    mode_d = min(counts, key=lambda d: (-counts[d], d))  # most common degree; ties -> smaller degree
    below_mean = sum(1 for d in values if d < mean)

    # Widen the bins automatically if the exact histogram would be too long to return.
    width = bin_width
    histogram = _histogram(counts, max_d, width)
    auto_widened = len(histogram) > MAX_BINS
    if auto_widened:
        width = math.ceil((max_d + 1) / MAX_BINS)
        histogram = _histogram(counts, max_d, width)

    hubs = sorted((v for v in deg if deg[v] == max_d))
    result = {
        "graph_id": graph_id,
        "directed": g.directed,
        "degree_type": kind,
        "number_of_nodes": n,
        "number_of_edges": g.number_of_edges(),
        "min_degree": min_d,
        "max_degree": max_d,
        "mean_degree": round(mean, 6),
        "median_degree": round(float(median), 6),
        "std_degree": round(std, 6),
        "most_common_degree": mode_d,
        "most_common_degree_count": counts[mode_d],
        "isolated_nodes": counts.get(0, 0),
        "fraction_below_mean": round(below_mean / n, 6),
        "max_degree_nodes": [node_ref(g, v, degree=max_d) for v in hubs[:MAX_HUBS]],
        "number_of_max_degree_nodes": len(hubs),
        "bin_width": width,
        "histogram": histogram,
    }

    name = {"total": "Degree", "in": "In-degree", "out": "Out-degree"}[kind]
    hub = result["max_degree_nodes"][0]["label"]
    more = f" and {len(hubs) - 1} other(s)" if len(hubs) > 1 else ""
    summary = (f"{name}s in '{graph_id}' range from {min_d} to {max_d} (mean {round(mean, 2)}, "
               f"median {round(float(median), 2)}); the most common is {mode_d} ({counts[mode_d]} of {n} nodes), "
               f"and {round(100 * below_mean / n)}% of nodes are below the mean. "
               f"The highest is {hub}{more} with {max_d}.")
    if not g.directed and degree_type != "total":
        summary += " The graph is undirected, so in- and out-degree equal the degree."
    if auto_widened:
        summary += f" The histogram uses bins of width {width} to keep the output small."
    return ok(result, summary)
