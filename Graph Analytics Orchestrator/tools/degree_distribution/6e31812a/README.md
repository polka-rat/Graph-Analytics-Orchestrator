# degree_distribution

**Author:** 6e31812a · **Tier:** easy · **Category:** structure

## What it computes
For every node it counts the edges that touch it (its degree), then counts how many nodes have each degree: the degree histogram. It also reports the minimum, maximum, mean and median degree, the most common degree, the number of isolated nodes, and the share of nodes below the mean, which shows whether the network is dominated by a few hubs. One pass over the adjacency lists: time O(V + E), memory O(V).

Degrees follow the NetworkX convention, so `histogram` equals `networkx.degree_histogram` with the zero counts dropped: in an undirected graph a self-loop counts twice; in a directed graph the total degree is in-degree + out-degree.

## When to use it
Questions about the overall shape of a network rather than about one node:
- "Do most airports have only a few routes, or are routes spread evenly?"
- "What is the typical number of friends in the karate club, and how many members have just one?"

To rank individual nodes, use `degree_centrality` or `node_degree` instead.

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| mode | string | `total` | `total` = all edges (in + out on directed graphs); `in` = incoming; `out` = outgoing. `in`/`out` need a directed graph. |
| bins | integer | none | 1 to 100. If set, degrees are grouped into this many equal-width ranges instead of one row per degree. |

## Output
`result` is an object:

```json
{"graph_id": "karate", "directed": false, "mode": "total", "nodes": 34, "edges": 78,
 "min_degree": 1, "max_degree": 17, "mean_degree": 4.588235, "median_degree": 3.0,
 "most_common_degree": {"degree": 2, "count": 11}, "isolated_nodes": 0,
 "share_below_mean": 0.705882, "binned": false,
 "histogram": [{"degree": 1, "count": 1}, {"degree": 2, "count": 11}, "..."]}
```

`histogram` lists only degrees that occur, in increasing order. With `bins` (or automatically, if the exact histogram would push the response past 8 KB) rows become `{"degree_min", "degree_max", "count"}` and `binned` is `true`. On the provided datasets the exact histogram always fits (airports: 5.6 KB). No `result_graph_id`: the tool does not create a subgraph.

## Graphs it supports
Directed and undirected; weighted or not (weights are ignored, only edges are counted). Works on subgraphs registered by other tools. A graph whose nodes have no edges gives a single row with degree 0.

## Errors
- Unknown `graph_id` → use `list_graphs`.
- Unknown parameter (for example `top_k`) → the error lists the accepted parameters.
- `mode` not one of `total`, `in`, `out`.
- `mode='in'` or `'out'` on an undirected graph → use `mode='total'`.
- `bins` not a whole number from 1 to 100.
- A graph with no nodes (for example an empty filtered subgraph).
