# Minimum Spanning Tree

**Author:** 5c98c8eb · **Tier:** medium · **Category:** structure

## What it computes

Computes a minimum spanning tree for a connected, undirected graph using Kruskal's algorithm. For disconnected graphs, it computes a minimum spanning forest. Edges are sorted by weight, with deterministic endpoint-based tie-breaking.

Time complexity: O(E log E), where E is the number of edges.

## When to use it

Use this tool to find a minimum-cost set of edges connecting all nodes in an undirected graph.

Example questions:
- What is the minimum spanning tree of the karate graph?
- What is the minimum total edge weight needed to connect the Les Miserables character network?

## Parameters

| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | required | Id of the graph |
| top_k | integer | 10 | Maximum number of selected edges displayed, from 1 to 100 |

## Output

The result contains the original graph ID, node and edge counts, selected edge count, total forest weight, whether the graph has a spanning tree, component count, and the displayed selected edges. Each edge includes source and target node references and its weight. `edges_truncated` indicates whether some selected edges were omitted from the displayed list.

The tool registers a result edge-subgraph when at least one edge is selected and returns its ID as `result_graph_id`. Isolated nodes are not included in that edge-subgraph.

## Graphs it supports

Supports undirected weighted and unweighted graphs. Unweighted edges are treated as having weight 1.0. Directed graphs are rejected with a helpful error. Disconnected undirected graphs produce a minimum spanning forest.

## Errors

Returns an error for an unknown graph, directed graphs, invalid `top_k`, or unexpected parameters.
