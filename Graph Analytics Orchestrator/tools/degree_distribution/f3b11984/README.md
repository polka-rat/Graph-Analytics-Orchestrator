# degree_distribution

**Author:** f3b11984 · **Tier:** easy · **Category:** structure

## What it computes
The degree of every node (number of edges at the node), grouped into a histogram, together with the minimum, maximum, mean, median and most common degree. One pass over the nodes: O(V + E) time.

## When to use it
Questions about how connections are spread across a network:
- "Do most nodes have only a few connections?"
- "Is this network dominated by a few hubs?" (compare the median with the maximum)

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| mode | string | `total` | Directed graphs only: `total` (in + out, the NetworkX `degree`), `in` or `out` |
| bin_width | integer | 1 | Degrees grouped per histogram bin; raised automatically if more than 40 bins would be needed |
| top_k | integer | 10 | How many highest-degree nodes to list (1 to 100) |

## Output
`result` is an object:
```json
{"mode": "total", "bin_width": 1,
 "statistics": {"nodes": 34, "min": 1, "max": 17, "mean": 4.5882, "median": 3.0,
                "most_common_degree": 2, "nodes_with_most_common_degree": 11},
 "histogram": [{"degree": 1, "degree_max": 1, "count": 1, "fraction": 0.0294}, "..."],
 "top_nodes": [{"id": "m34", "label": "Member 34 (administrator)", "degree": 17}, "..."]}
```
`histogram` bins are sorted by degree and empty bins are left out; each bin covers `degree` to `degree_max` inclusive. `top_nodes` is ordered by degree, ties broken by node id. `result_graph_id` is `null`.

## Graphs it supports
Directed and undirected graphs. Edge weights are ignored: degree counts edges, not weight. An undirected self-loop counts twice (as in NetworkX).

## Errors
- Unknown graph id: use `list_graphs`.
- `mode` not in `total`/`in`/`out`, or `in`/`out` on an undirected graph.
- `bin_width` not a whole number of at least 1; `top_k` outside 1 to 100.
- Unknown parameter names.
- A graph with no nodes.
