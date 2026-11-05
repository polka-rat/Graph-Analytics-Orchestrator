# connected_components

**Author:** 991d1029 · **Tier:** easy · **Category:** community

## What it computes
Partitions the nodes into connected components using an iterative DFS over the undirected graph. Time O(V + E).

## When to use it
- "Is the karate club network connected?"
- "What is the largest connected part of the Les Misérables network?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| top_k | integer | 10 | How many of the largest components to return (1 to 100) |

## Output
`result` is a list sorted by size (desc), ties by smallest node id: `{"component", "size", "graph_id", "nodes": [first 10 node refs by id]}`. Each component is registered as a subgraph; `result_graph_id` is the largest one.

## Graphs it supports
Undirected only (weighted or not; weights ignored). Directed graphs return an error pointing to `strongly_connected_components`. Isolated nodes are components of size 1.

## Errors
Unknown graph, unknown parameter, invalid `top_k`, directed graph.
