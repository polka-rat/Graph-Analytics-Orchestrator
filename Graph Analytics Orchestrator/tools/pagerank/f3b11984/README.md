# pagerank

**Author:** f3b11984 · **Tier:** medium · **Category:** centrality

## What it computes
PageRank by power iteration. Every node starts with rank 1/n; each step a node keeps `(1 - damping)/n` plus `damping` times the rank that flows to it along edges, where each node splits its rank over its out-edges in proportion to the edge weights (equally if unweighted). Nodes with no out-edges ("dangling") spread their rank evenly over all nodes, as NetworkX does. Iteration stops when the total change drops below 1e-12 (at most 1000 iterations). Undirected edges carry rank in both directions. Cost: O(iterations × E), implemented with NumPy.

## When to use it
- "Which airports are the most important in the network?"
- "Which characters are the most influential?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| damping | number | 0.85 | Probability of following a link, from 0 up to (not including) 1 |
| top_k | integer | 10 | How many top nodes to return (1 to 100) |
| weighted | boolean | true | Use edge weights as link strength when the graph has them; `false` treats every edge equally |

## Output
`result` is a list of the top_k nodes, best first, ties broken by node id:
```json
[{"id": "m34", "label": "Member 34 (administrator)", "rank": 1, "score": 0.10091918}]
```
Scores over all nodes sum to 1. The `summary` states the top node, the damping, whether weights were used and the number of iterations. `result_graph_id` is `null`.

## Graphs it supports
Directed and undirected, weighted and unweighted. The default `weighted=true` matches NetworkX. On `airports` the weight is a distance in km, not a strength of connection, so pass `weighted=false` to rank airports by route structure alone. Negative weights are rejected.

## Errors
- Unknown graph id: use `list_graphs`.
- `damping` outside [0, 1) or not a number; `top_k` outside 1 to 100; `weighted` not a boolean.
- Negative edge weights (retry with `weighted=false`).
- Unknown parameter names.
- A graph with no nodes; failure to converge (not expected for damping below 1).
