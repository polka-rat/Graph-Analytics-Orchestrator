# Closeness Centrality

**Author:** 7cc0c2d7 · **Tier:** Medium · **Category:** Centrality

## What it computes
This tool calculates closeness centrality for each node using breadth-first search (BFS). The score is the number of other reachable nodes divided by the sum of their shortest-path distances from the node. A higher score indicates that a node can reach other nodes in fewer steps.

For a graph with V nodes and E edges, the time complexity is O(V(V + E)).

## When to use it
Use this tool to identify nodes that are close to other nodes in a network.

Example questions:
- Which nodes have the highest closeness centrality in the Karate Club graph?
- Which airports can reach other airports in relatively few flights?

## Parameters

| Name | Type | Default | Meaning |
|---|---|---|---|
| graph_id | string | Required | Id of the graph |
| top_k | integer | 10 | Number of top results to return (1 to 100) |

## Output
Returns up to `top_k` node references, each containing an ID, label, and closeness centrality score. It does not produce a result graph.

## Graphs it supports
Supports directed and undirected, unweighted graphs. Directed graphs are traversed using outgoing edges. Each edge counts as one step; edge weights are not used.

## Errors
Returns an error if the graph does not exist, an unknown parameter is supplied, `top_k` is invalid, or the graph has no nodes.