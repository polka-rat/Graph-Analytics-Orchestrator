
# Closeness Centrality

**Author:** afc500fb · **Tier:** Medium · **Category:** Centrality

## What it computes

Calculates closeness centrality for one specified node. It finds shortest-path distances from all nodes that can reach the selected node, then calculates the normalized reciprocal of the total distance.

For a graph with N nodes, let r be the number of nodes that can reach the selected node, including the selected node itself. The score uses NetworkX's improved normalization:

C(v) = ((r - 1) / sum_of_distances) * ((r - 1) / (N - 1))

The score is zero for a graph containing one node or when no other node can reach the selected node.

Time complexity:
- Unweighted graphs: O(V + E).
- Weighted graphs: O((V + E) log V), using Dijkstra's algorithm.

## When to use it

Use this tool to measure how close a particular node is to the rest of the graph.

Example questions:
- How central is node m1 in the Karate Club graph?
- How easily can other airports reach MAA?

## Parameters

| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | Required | ID of the graph |
| node | string | Required | Node whose closeness score is calculated |

## Output

Returns one node reference containing its ID, label, closeness score rounded to six decimal places, and the number of other nodes that can reach it.

Example:

{
  "id": "m1",
  "label": "Node 1",
  "score": 0.5,
  "reachable_nodes": 2
}

The actual label and score depend on the input graph.

No result graph is registered.

## Graphs it supports

Supports directed and undirected, weighted and unweighted graphs.

- Directed graphs: follows NetworkX's default convention, measuring distances toward the selected node.
- Unweighted graphs: every edge has distance 1.
- Weighted graphs: edge weights are interpreted as distances and must be finite and strictly positive.
- Disconnected graphs: uses NetworkX's improved normalization, accounting for the number of nodes that can reach the selected node.

## Errors

- Unknown graph ID: use list_graphs to find a valid graph.
- Unknown node ID: use lookup_node to find a valid node ID.
- Unknown parameter: remove unsupported parameters.
- Invalid weighted edge distance: correct the graph so every distance is finite and strictly positive.
