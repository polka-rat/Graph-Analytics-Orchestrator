# degree_distribution

**Author:** c4576e71 · **Tier:** easy · **Category:** structure

## What it computes
The degree of every node, the histogram of those degrees, and summary statistics (min, max, mean, median, most common degree, number of isolated nodes). It is a single pass over the nodes, O(V + E). If the degrees span more than `max_bins` values they are grouped into equal-width bins.

## When to use it
- "Do most nodes have only a few connections?"
- "Is this network dominated by a few hubs?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| mode | string | total | Directed graphs only: `in`, `out` or `total` (in + out, as NetworkX `degree`) |
| max_bins | integer | 20 | Maximum number of histogram bins (1 to 100) |

## Output
`result` is an object with `mode`, `num_nodes`, `min_degree`, `max_degree`, `mean_degree`, `median_degree`, `most_common_degree`, `isolated_nodes`, `bin_width`, `histogram` (a list of `{low, high, count, fraction}`; `low == high` when `bin_width` is 1) and `highest_degree_nodes` (five nodes with id, label and degree, ties by node id). It returns no `result_graph_id`.

## Graphs it supports
Directed and undirected, weighted or not (weights are ignored). Degree counts distinct neighbours.

## Errors
- Unknown graph id.
- `mode` not one of `total`, `in`, `out`.
- `max_bins` not a whole number from 1 to 100.
- Unknown extra parameter.
- A graph with no nodes.
