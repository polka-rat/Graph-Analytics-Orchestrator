# minimum_spanning_tree

**Author:** b2eb4e3d · **Tier:** medium · **Category:** structure

## What it computes
Finds a minimum spanning tree with Kruskal's algorithm. Edges are sorted by (weight, smaller node id, larger node id) and added one by one, skipping any edge that would close a cycle. A union-find structure with path compression and union by size detects cycles. Time complexity is O(E log E) and memory is O(V + E). If the graph is disconnected, the result is a minimum spanning forest with one tree per component.

## When to use it
Use it to find the cheapest way to connect all nodes, or the total weight of that connection. Example questions:
- "What is the total weight of the minimum spanning tree of the karate club network?"
- "Which links form the cheapest backbone connecting the airports?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| top_k | integer | 10 | How many tree edges to list, lightest first (1 to 100) |

## Output
`result` contains:
- `total_weight`: sum of the tree edge weights, rounded to 6 decimals
- `num_nodes`, `num_edges`, `num_components`, `is_connected`, `weighted`
- `edges`: up to `top_k` tree edges, each `{source, target, weight}` where source and target are `{id, label}`, sorted by weight and then by node ids ascending
- `truncated`: true if `edges` lists fewer edges than `num_edges`

The tree (or forest) is registered as a subgraph and its id is returned as `result_graph_id`. When the tree has no edges (a single node, or a graph without edges), `result_graph_id` is null. Repeating the same query returns the same subgraph id. The edge list is also trimmed if needed to keep the output under 8 KB.

Abridged example for `graph_id=karate`:

    {"total_weight": 33.0, "num_nodes": 34, "num_edges": 33, "num_components": 1,
     "is_connected": true, "weighted": false,
     "edges": [{"source": {"id": "...", "label": "..."}, "target": {"id": "...", "label": "..."}, "weight": 1.0}, "..."],
     "truncated": true}

## Graphs it supports
Undirected and directed graphs, weighted or unweighted. Unweighted edges count 1.0. On a directed graph, directions are ignored and a pair joined both ways uses the smaller weight; tree edges are reported in their original direction. Negative weights are fine. Self-loops are ignored. Non-finite weights (NaN or infinity) return an error.

## Errors
Every error is returned as `error(...)`, never raised:
- Unknown or non-string `graph_id`: use `list_graphs` to see the available graphs.
- `top_k` is not a whole number from 1 to 100 (booleans, strings and floats are rejected).
- The graph has no nodes.
- An edge has a non-finite weight.
- An unknown parameter is passed.
- The spanning tree could not be registered as a subgraph.