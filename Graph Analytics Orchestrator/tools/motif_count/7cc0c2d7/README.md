# motif_count

**Author:** 7cc0c2d7 · **Tier:** hard · **Category:** structure

## What it computes

This tool counts triangle motifs. A triangle is a set of three distinct nodes in which all three pairs are connected by edges. Each triangle is counted exactly once.

For directed graphs, edge directions are ignored. Edge weights are also ignored. The straightforward implementation takes O(V^3) time in the worst case, where V is the number of nodes.

## When to use it

Use this tool to understand how many tightly connected groups of three nodes occur in a graph.

Example questions:
- How many triangle motifs exist in the karate graph?
- How many groups of three mutually connected nodes exist in this network?

## Parameters

| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |

## Output

The result contains the triangle count, number of nodes, and number of edges. It does not return a subgraph.

Example:
`{"triangle_count": 5, "node_count": 10, "edge_count": 12}`

## Graphs it supports

Supports directed and undirected, weighted and unweighted graphs. Direction and weights are ignored for triangle counting. Self-loops do not contribute to triangles.

## Errors

- Unknown graph ID: the graph does not exist in the graph store.
- Unknown parameter: a parameter other than graph_id was provided.
