# clustering_coefficient

**Author:** 6ae0e02c · **Tier:** easy · **Category:** structure

## What it computes
For a node with k neighbours, the local clustering coefficient is the fraction of pairs of its neighbours that are themselves connected: C(v) = 2·links / (k(k−1)), and 0 if k < 2. The graph average is the mean over all nodes (zeros included), matching NetworkX's `average_clustering`. For directed graphs it uses Fagiolo's directed definition (the one `nx.clustering` uses on a DiGraph), which counts triangles in either direction. Self-loops are ignored. Time: O(sum over nodes of k · average neighbour-set intersection cost), fast for the provided graphs.

## When to use it
- "How likely is it that two friends of the instructor are friends with each other?" (`karate`, node `m1`)
- "Which airports have the most tightly connected neighbourhood?" (`airports`)

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| node | string | none | Node id; if given, only this node is returned |
| top_k | integer | 10 | How many most-clustered nodes to return (1 to 100); ignored when `node` is given |

## Output
`result` = `{"average_clustering": float, "graph_type": "undirected" | "directed (Fagiolo)", "nodes": [{"id", "label", "clustering", "degree"}]}`, sorted by clustering descending, ties by node id. `degree` is the number of distinct neighbours (undirected) or in-degree plus out-degree (directed). Floats are rounded to 6 places. If `top_k` is large and the output would exceed 8 KB, the lowest-ranked entries are dropped and the summary says so. It does not return `result_graph_id`.

## Graphs it supports
Directed and undirected, weighted or not (weights are ignored).

## Errors
- Unknown `graph_id`, or a `graph_id` that is not a string.
- `node` is not a node of the graph.
- `top_k` is not a whole number from 1 to 100 (booleans are rejected).
- Any unknown parameter name.
- A graph with no nodes.
