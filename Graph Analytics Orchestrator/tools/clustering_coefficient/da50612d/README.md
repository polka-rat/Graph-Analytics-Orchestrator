# clustering_coefficient

**Author:** da50612d · **Tier:** easy · **Category:** structure

## What it computes
The local clustering coefficient of a node: the share of pairs of its neighbours that are linked to each other. On an undirected graph, c(u) = 2·T(u) / (deg(u)·(deg(u) − 1)), where T(u) is the number of triangles through u. A node with fewer than two neighbours gets 0. The graph's average clustering is the mean over all nodes, zeros included (the same as `networkx.average_clustering`).

- **Directed graphs** use Fagiolo's (2007) definition, the one NetworkX uses: with S = A + Aᵀ, c(u) = (S³)ᵤᵤ / (2·(d_tot(d_tot − 1) − 2·d_recip)), so every orientation of a triangle counts and reciprocal pairs are not counted as triangles.
- **Weighted (`weighted=true`)**: edge weights are divided by the largest weight, and each triangle contributes the cube root of the product of its three weights (the geometric mean, Onnela et al. 2005), as in `networkx.clustering(G, weight="weight")`.

Implementation: the adjacency matrix is built once with NumPy, and the diagonal of S³ is read off as `((S @ S) * Sᵀ).sum(axis=1)`. Time O(n³) with a fast matrix product (about 0.1 s on `airports`, n = 500), memory O(n²).

## When to use it
Questions about how tightly knit a neighbourhood or a whole network is:
- "How tightly knit is the instructor's circle in the karate club?"
- "Do the airports connected to Chennai also connect to each other?"
- "Which characters in Les Misérables sit in the most closed groups?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| node | string | none | A node id (from `lookup_node`). If given, return that node's values; if not, return the graph average and the top_k nodes |
| top_k | integer | 10 | How many of the most clustered nodes to return (1 to 100) when no node is given |
| weighted | boolean | false | Use edge weights (weighted clustering) |

## Output
With `node`:
```json
{"node": {"id": "m1", "label": "Member 1 (instructor)", "clustering": 0.15, "degree": 16, "triangles": 18},
 "average_clustering": 0.570638, "directed": false, "weighted": false}
```
On a directed graph the node entry has `directed_triangles` (Fagiolo's count) instead of `triangles`, and `degree` is in-degree plus out-degree.

Without `node`:
```json
{"average_clustering": 0.570638, "nodes": 34, "nodes_with_zero_clustering": 2,
 "directed": false, "weighted": false,
 "top": [{"id": "m13", "label": "Member 13", "clustering": 1.0, "degree": 2}, ...]}
```
`top` is sorted by clustering (highest first). Equal values are ordered by node id. Values are rounded to 6 decimals. If `top_k` entries would push the response past 8 KB (long airport names), the list is shortened, and the summary says how many entries are shown. `result_graph_id` is always `null`.

## Graphs it supports
Undirected and directed, weighted and unweighted, including subgraphs registered by other tools. Weights are ignored unless `weighted=true`; on an unweighted graph `weighted=true` gives the same values, and the summary says so. Self-loops are ignored.

## Errors
| Error | Why |
| --- | --- |
| `No graph with id '…'` | Unknown `graph_id`; use `list_graphs` |
| `Node '…' is not in graph '…'. Use lookup_node…` | `node` is not a node id (for example a name) |
| `top_k must be a whole number from 1 to 100` | Bad `top_k` |
| `weighted must be true or false` | `weighted` is not a boolean |
| `Unknown parameter(s): …` | A parameter this tool does not take |
| `Graph '…' has no nodes` | Empty graph |
