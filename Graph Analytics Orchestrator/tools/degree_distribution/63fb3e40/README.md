# degree_distribution

**Author:** 63fb3e40 · **Tier:** easy · **Category:** structure

## What it computes
The degree of every node, then a histogram of how many nodes have each degree, together with summary
statistics (min, max, mean, median, population standard deviation, most common degree, isolated nodes,
fraction of nodes below the mean) and the highest-degree nodes. Degree counts edges, not weights; an
undirected self-loop counts twice, as in NetworkX. Time complexity is O(n + m).

## When to use it
Questions about the overall shape of a network's connectivity rather than about one node:
- "Do most characters in Les Misérables appear with only a few others?"
- "Is the airport network dominated by a few hubs, or do airports have similar numbers of routes?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| degree_type | string | `total` | Directed graphs only: `total` (in + out), `in` or `out`. Ignored for undirected graphs |
| bin_width | integer | 1 | Width of each histogram bin (1 to 10000); 1 gives one bin per exact degree |

## Output
`result` is an object with the statistics and the histogram (non-empty bins only, in increasing order
of degree). It does not return a subgraph (`result_graph_id` is null).

```json
{"graph_id": "karate", "directed": false, "degree_type": "total",
 "number_of_nodes": 34, "number_of_edges": 78,
 "min_degree": 1, "max_degree": 17, "mean_degree": 4.588235, "median_degree": 3.0, "std_degree": 3.820361,
 "most_common_degree": 2, "most_common_degree_count": 11, "isolated_nodes": 0, "fraction_below_mean": 0.705882,
 "max_degree_nodes": [{"id": "m34", "label": "Member 34 (administrator)", "degree": 17}], "number_of_max_degree_nodes": 1,
 "bin_width": 1,
 "histogram": [{"degree": 1, "count": 1}, {"degree": 2, "count": 11}, "..."]}
```

With `bin_width` > 1 each bin is `{"degree_from": a, "degree_to": b, "count": c}`. If the exact
histogram would have more than 200 non-empty bins, the bin width is widened automatically (and the
summary says so) to keep the response under 8 KB. At most five highest-degree nodes are listed, sorted
by id; `number_of_max_degree_nodes` gives the full count.

## Graphs it supports
Directed and undirected, weighted and unweighted (weights are ignored). On an undirected graph,
`degree_type` `in` or `out` gives the ordinary degree and the summary says so.

## Errors
- Unknown `graph_id`: use list_graphs to see the available graphs.
- `degree_type` not one of `total`, `in`, `out`.
- `bin_width` not a whole number from 1 to 10000.
- The graph has no nodes (e.g. an empty registered subgraph).
- Unknown parameters.
