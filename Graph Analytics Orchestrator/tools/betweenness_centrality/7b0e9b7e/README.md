# betweenness_centrality

**Author:** 7b0e9b7e · **Tier:** hard · **Category:** centrality

## What it computes
The betweenness of a node `v` is the sum, over all pairs of other nodes `(s, t)`, of the fraction of shortest `s`→`t` paths that pass through `v`. It is computed exactly with Brandes' algorithm: from each source, one breadth-first search counts the shortest paths to every node, then a backward pass from the farthest nodes adds up each node's share. Scores are normalized by `(n - 1)(n - 2)`, as in NetworkX, so they lie between 0 and 1. Time complexity: O(n · m) on unweighted graphs, under a second on `airports`.

## When to use it
Questions about brokers, bridges and bottlenecks, for example:
- "Who are the key brokers between the two groups of the karate club?"
- "Which airport is the most important transfer hub?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| top_k | integer | 10 | How many results to return (1 to 100) |

## Output
A list of the top_k nodes, highest betweenness first (ties broken by node id), each with `betweenness` (0 to 1, rounded to 6 decimals). If `top_k` nodes with long labels would exceed the 8 KB output limit (e.g. `top_k=100` on airports), fewer nodes are listed and the summary says so. `result_graph_id` is always null.

```json
[{"id": "m1", "label": "Member 1 (instructor)", "betweenness": 0.437635}]
```

## Graphs it supports
Undirected and directed graphs (paths follow edge direction), connected or not. Edge weights are ignored: shortest paths are counted in hops. Graphs with two or fewer nodes give 0 for every node.

## Errors
- Unknown `graph_id`: use list_graphs to see the graphs.
- `top_k` not a whole number from 1 to 100.
- An unknown parameter name.
- A graph with no nodes.
