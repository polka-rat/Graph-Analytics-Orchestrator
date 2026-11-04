# hits

**Author:** f9857550 (Cheripelly Karthik) · **Tier:** medium · **Category:** centrality

## What it computes
Kleinberg's HITS by power iteration on the adjacency matrix A (A[i, j] = 1 for i → j): starting from uniform hub scores, repeat `authority = Aᵀ·hub`, `hub = A·authority`, normalising each to sum 1, until the total change in hub scores is below `tol` (or `max_iter` steps). This converges to the principal eigenvectors of AᵀA (authorities) and AAᵀ (hubs). Each step costs O(V²) with NumPy dense matrices, which is well under a second for the 500-node airports graph.

## When to use it
- "Which airports send flights to the most important destinations?" (hubs)
- "Which courses are the most authoritative prerequisites?" (authorities)

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| top_k | integer | 10 | How many nodes to return (1 to 100) |
| sort_by | string | authority | Rank by `authority` or `hub` |
| max_iter | integer | 1000 | Maximum power-iteration steps |
| tol | number | 1e-10 | Convergence threshold on the L1 change in hub scores |
| use_weights | boolean | false | Use edge weights as link strengths |

## Output
`result` is a list of nodes, ties broken by node id, scores rounded to 6 places:
```json
[{"id": "AMS", "label": "Amsterdam Airport Schiphol", "authority": 0.010271, "hub": 0.010116}]
```
If 100 long labels would exceed 8 KB, the lowest-ranked entries are dropped and the summary says so. No `result_graph_id`.

## Graphs it supports
Directed graphs (its natural setting). Undirected graphs work too, but hub = authority there (the summary says so). Weighted graphs are treated as unweighted unless `use_weights` is true.

## Errors
- Unknown `graph_id`; bad `top_k`, `sort_by`, `max_iter`, `tol` or `use_weights`; unknown extra parameter.
- A graph with no edges (scores undefined).
- Negative weights with `use_weights=true`.
- Non-convergence is not an error: the scores are returned with a warning in the summary.
