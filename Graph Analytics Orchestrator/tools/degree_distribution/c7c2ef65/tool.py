"""Degree distribution: how many nodes have each degree, plus the minimum, maximum and mean degree.

Highlights:
- One pass over the nodes, O(V + E); reads degrees straight from the adjacency, so even airports takes milliseconds.
- mode = total | in | out on directed graphs, so it also answers "arriving" and "departing" questions.
  total (the default) equals nx.degree_histogram, with in + out for directed graphs.
- Histogram lists only the degrees that occur, as sorted {degree, count} entries: compact (under 8 KB even for
  airports' 173 distinct degrees) and readable by an LLM without index arithmetic.
- Mean rounded to 6 decimals; the summary names the range, the mean and the most common degree (ties by
  smallest degree), so the LLM can answer from the summary alone.
- Clear errors for an unknown graph, a bad mode, in/out on an undirected graph, and unknown parameters.
"""
from collections import Counter

from graphkit.contract import error, get_graph, ok

MODES = ("total", "in", "out")


def _count(n, word, plural=None):
    """'1 node', '2 nodes'."""
    return f"{n} {word if n == 1 else plural or word + 's'}"


def _degree(g, node, mode):
    """Degree of `node` for this mode; an undirected graph has only one kind."""
    if not g.directed:
        return len(g.undirected_neighbors(node))
    if mode == "in":
        return len(g.in_neighbors(node))
    if mode == "out":
        return len(g.out_neighbors(node))
    return len(g.in_neighbors(node)) + len(g.out_neighbors(node))


def run(store, graph_id, mode="total", **params):
    # Validate the call before doing any work.
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. degree_distribution takes graph_id and mode.")
    if mode not in MODES:
        return error(f"mode must be one of {', '.join(MODES)}; got {mode!r}.")
    if mode != "total" and not g.directed:
        return error(f"'{graph_id}' is undirected, so in- and out-degree are the same as degree. Use mode='total'.")
    n = g.number_of_nodes()
    if n == 0:
        return error(f"Graph '{graph_id}' has no nodes, so it has no degree distribution.")

    # One pass: degree of every node, then how many nodes share each degree.
    degrees = [_degree(g, node, mode) for node in g.nodes()]
    counts = Counter(degrees)
    histogram = [{"degree": d, "count": counts[d]} for d in sorted(counts)]
    lo, hi, mean = min(degrees), max(degrees), round(sum(degrees) / n, 6)
    most_common = min(counts, key=lambda d: (-counts[d], d))  # ties -> smaller degree
    result = {"mode": mode if g.directed else "total", "num_nodes": n, "min_degree": lo, "max_degree": hi,
              "mean_degree": mean, "histogram": histogram}

    kind = {"total": "degree", "in": "in-degree", "out": "out-degree"}[result["mode"]]
    summary = (f"In '{graph_id}', {kind} ranges from {lo} to {hi} with mean {mean} over {_count(n, 'node')}; "
               f"the most common {kind} is {most_common} ({_count(counts[most_common], 'node')}).")
    return ok(result, summary)
