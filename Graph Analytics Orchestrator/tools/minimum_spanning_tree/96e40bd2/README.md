# minimum_spanning_tree

**Author:** 96e40bd2 · **Tier:** medium · **Category:** structure (returns a subgraph)

## What it computes
A minimum spanning tree (MST): the set of edges that connects every node with the smallest possible total weight, using Kruskal's algorithm with a union-find structure. Edges are sorted by (weight, node ids), so ties are always resolved the same way. Time O(E log E), memory O(V + E). If the graph is disconnected the result is a minimum spanning forest.

## When to use it
- "What is the cheapest way to connect all the sites?" (graph `lesmis`)
- "How many edges and what total weight does the backbone of the karate club network have?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of an undirected graph |
| top_k | integer | 10 | How many tree edges to list (1 to 100), heaviest first |

## Output
`result` is a list of tree edges `{"source": {id, label}, "target": {id, label}, "weight": w}`, heaviest first, at most `top_k` (and fewer if needed to stay under 8 KB). The summary gives the number of edges and the total weight. `result_graph_id` is the id of the whole tree registered with the store (all edges, not just the listed ones), so another tool can run on it.
```json
{"status": "ok",
 "result": [{"source": {"id": "c63", "label": "Myriel"}, "target": {"id": "c74", "label": "Valjean"}, "weight": 5.0}],
 "summary": "The minimum spanning tree of 'lesmis' has 76 edges and total weight 105.0. Showing the 1 heaviest of 76 edges.",
 "result_graph_id": "lesmis~1", "error": null}
```

## Graphs it supports
Undirected graphs, weighted or unweighted (unweighted edges count as 1, and the summary says so). Directed graphs give an error. Disconnected graphs give a forest.

## Errors
- Unknown graph: use `list_graphs`.
- Directed graph: says an undirected graph is needed.
- Graph with no edges: says there is no spanning tree.
- Invalid `top_k` (not a whole number from 1 to 100) or unknown parameter.
