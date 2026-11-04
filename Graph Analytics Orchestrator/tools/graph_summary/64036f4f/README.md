# graph_summary

**Author:** Hayagriv (64036f4f) · **Tier:** easy · **Category:** structure

## What it computes

This tool reports node and edge counts, density, average degree, and whether a graph is directed or weighted. Density uses the number of possible directed or undirected edges as appropriate. The computation takes O(1) time because the graph store maintains the counts.

## When to use it

Use it for questions such as “How big is the karate network?” or “How dense is the airports graph?”

## Parameters

| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | required | Id of the graph |

## Output

`result` contains `node_count`, `edge_count`, `density`, `average_degree`, `directed`, and `weighted`. Directed graphs also include average in-degree and average out-degree. It does not create a result graph.

## Graphs it supports

All directed, undirected, weighted, and unweighted graphs are supported. Edge weights do not change structural density or degree counts.

## Errors

An unknown graph id or any unsupported parameter returns a contract error with corrective guidance.
