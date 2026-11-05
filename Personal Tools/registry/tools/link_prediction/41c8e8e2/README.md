# link_prediction

**Author:** 41c8e8e2 · **Tier:** medium · **Category:** structure

## What it computes
Scores every pair of nodes that is **not** yet connected and returns the highest-scoring pairs as the most likely missing links. All pair scores come from NumPy matrix products on the adjacency matrix A (O(n³) worst case, well under a second for the 500-node airports graph).

| method | score for pair (u, v) |
| --- | --- |
| `adamic_adar` (default) | Σ over common neighbours w of 1 / ln(deg w) |
| `common_neighbors` | number of common neighbours |
| `jaccard` | common neighbours / neighbours of either |
| `resource_allocation` | Σ over common neighbours w of 1 / deg w |
| `preferential_attachment` | deg u × deg v |

## When to use it
- "Who should Member 1 connect with next?" (`node="m1"`)
- "Which friendships in the karate club are probably missing?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| method | string | adamic_adar | One of the five methods above |
| node | string | none | Only suggest links involving this node |
| top_k | integer | 10 | How many pairs to return (1 to 100) |

## Output
`result` is a list of `{"source": {id, label}, "target": {id, label}, "score": float}`, best first. Scores are rounded to 6 places; ties are broken by (source id, target id) ascending, with the two ids of a graph-wide pair ordered so that source < target. With `node` set, `source` is always that node. Only pairs with a positive score are returned (so the list can be shorter than `top_k`). If the 8 KB output limit would be exceeded the list is shortened and the summary says so. `result_graph_id` is `null`.

## Graphs it supports
Any graph. Direction and weights are ignored: a pair is "connected" if an edge exists in either direction, and the neighbourhoods used are the undirected neighbours. Self-loops are ignored. Graphs larger than 3,000 nodes are refused.

## Errors
- Unknown graph, unknown `node`, bad `top_k`, unknown `method` or unknown parameter.
- Graph with fewer than 3 nodes, or more than 3,000 nodes.
- If no pair has a positive score the call succeeds with an empty list.
