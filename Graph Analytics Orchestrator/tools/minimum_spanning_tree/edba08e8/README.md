# minimum_spanning_tree

**Author:** edba08e8 · **Tier:** medium · **Category:** structure · **Returns a subgraph (↪)**

## What it computes
A minimum spanning tree using Kruskal's algorithm with a union-find (path compression + union by rank).
Time O(E log E). Edges are sorted by `(weight, u, v)`, so ties are broken by node id and the output is deterministic.

## When to use it
- "What is the cheapest way to connect all the sites?"
- "What is the minimum total weight needed to link every character in the network?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of an undirected graph |
| top_k | integer | 10 | How many tree edges to list (1 to 100), cheapest first |

## Output
```
{"total_weight": 123.0, "num_tree_edges": 76, "num_nodes": 77, "num_components": 1,
 "edges_returned": 10, "edges": [{"source": {id,label}, "target": {id,label}, "weight": 1.0}, ...]}
```
The full tree is registered with `store.edge_subgraph` and its id is returned in `result_graph_id`.
If listing `top_k` edges would exceed ~6.5 KB, fewer edges are listed (`edges_returned` says how many).

## Graphs it supports
Undirected graphs, weighted or unweighted (unweighted edges count as 1). Self-loops are ignored.
A disconnected graph gives a minimum spanning **forest**; `num_components` tells how many trees.

## Errors
- Unknown graph id; invalid `top_k`; unknown extra parameters.
- Directed graph: an MST is not defined, the error suggests an undirected graph.
- Graph with no edges.
