# graph_summary

**Author:** 2f7893e5 · **Tier:** easy · **Category:** structure

## What it computes
The basic size and density of one graph: node count n, edge count m, density, average degree, and the number of isolated nodes (no edges at all). One pass over the nodes, so O(n + m) overall; the counts n and m come straight from the store.

- **Density** is the fraction of possible edges that exist: m / (n(n−1)) for a directed graph, 2m / (n(n−1)) for an undirected one. With n ≤ 1 no edge between distinct nodes is possible, so density is 0 (as in NetworkX).
- **Average degree** is 2m / n: every edge adds 1 to the degree of both endpoints. For a directed graph this is the average of in-degree + out-degree; `avg_out_degree` and `avg_in_degree` (both m / n) are also returned.

## When to use it
Questions about a network as a whole, not about particular nodes:
- "How big is the airport network?"
- "Is the Les Misérables co-appearance network dense or sparse?"
- "On average, how many routes leave an airport?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph or registered subgraph |

## Output
`result` is one object (no node list), and `result_graph_id` is always `null`:

```json
{"graph_id": "airports", "directed": true, "weighted": true, "nodes": 500, "edges": 20058,
 "density": 0.080393, "avg_degree": 80.232, "isolated_nodes": 0,
 "avg_out_degree": 40.116, "avg_in_degree": 40.116}
```

`avg_out_degree` and `avg_in_degree` appear only for directed graphs. Floats are rounded to 6 decimal places.

## Graphs it supports
Every graph: directed or undirected, weighted or unweighted (weights are not used), including subgraphs registered by other tools (e.g. `filter_nodes`). A graph with 0 or 1 nodes gives density 0 and a summary saying so; an empty graph also gives average degree 0.

## Errors
- Unknown `graph_id`: tells you to call `list_graphs`.
- Any parameter other than `graph_id`: names the unknown parameter.
