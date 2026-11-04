# hits

**Author:** 219c8a12 · **Tier:** medium · **Category:** centrality

## What it computes
**HITS** (Kleinberg's Hyperlink-Induced Topic Search) gives every node two scores, using the adjacency matrix A with A[u, v] = weight of edge u→v:
- **Authority**: a node is a good authority if good hubs point to it. a = Aᵀh.
- **Hub**: a node is a good hub if it points to good authorities. h = Aa.

At convergence, a is the principal eigenvector of AᵀA and h is the principal eigenvector of AAᵀ.

**Algorithm (power iteration, same scheme as NetworkX 3.x `nx.hits`).**
1. Map nodes to indices and store the edges as NumPy arrays `src`, `dst` and `w`. An undirected edge is stored in both directions, except a self-loop, which is stored once (as in NetworkX's adjacency matrix). No dense n×n matrix is built.
2. Start from h = 1/n.
3. Each step computes `a = bincount(dst, w·h[src])` (that is, Aᵀh), then `h = bincount(src, w·a[dst])` (that is, Aa), then rescales h so its largest entry is 1.
4. Stop when the L1 change in h is below `tol`, or after `max_iter` steps.
5. Finally, each vector is divided by its sum (default) or by its maximum.

Each iteration costs O(n + m). On `airports` (500 nodes, 20,058 edges) the tool converges in 14 iterations and takes under 0.01 s.

## When to use it
- "Which airports have routes to the most important destinations?" → best **hubs** on `airports`
- "Which pages / sources are the most authoritative?" → best **authorities**

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph (a dataset or a registered subgraph) |
| score | `"hub"`, `"authority"` or `"both"` | `"both"` | Which ranking(s) to return |
| top_k | integer | 10 | Nodes per ranking (1 to 100) |
| max_iter | integer | 100 | Maximum power iterations (1 to 100,000) |
| tol | number | 1e-8 | Stop when the L1 change of the max-scaled hub vector is below this (0 < tol < 1) |
| normalized | boolean | true | true: scores in each ranking sum to 1. false: the largest score is 1 |
| weighted | boolean | true | Use edge weights if the graph has them (as `nx.hits` does). false: every link counts 1 |

## Output
`result` is an object with these fields:
- `hubs` and/or `authorities`: lists of `{"id", "label", "hub", "authority"}`. Each list is sorted by its own score (descending), with ties broken by node id (ascending). Scores are rounded to 6 decimals.
- `iterations`: how many power iterations ran.
- `converged`: whether `tol` was reached.

If both full lists would push the response over 8 KB, they are shortened and the summary says so. `result_graph_id` is always `null`.

```json
{"status": "ok",
 "result": {"hubs": [{"id": "...", "label": "...", "hub": 0.0123, "authority": 0.0119}],
            "authorities": [...], "iterations": 14, "converged": true},
 "summary": "Among 500 nodes of 'airports', the top hub is ... and the top authority is .... Scores sum to 1 within each ranking; edge weights were used ...",
 "result_graph_id": null, "error": null}
```

## Graphs it supports
- **Directed:** the natural case.
- **Undirected:** allowed. A is symmetric, so hub and authority scores are **identical**, and the summary says so in case anyone reads the two lists as different.
- **Weighted:** weights are used by default, which matches NetworkX. Note that on `airports` the weight is the route distance in km, so long-haul routes count more. Use `weighted=false` to count routes equally.
- **Disconnected graphs / repeated top eigenvalue:** HITS can concentrate on one component. When the top eigenvalue of AᵀA is repeated (e.g. the bipartite `projects` graph), the eigenvector is not unique and the result depends on the start vector. The fixed uniform start keeps the output deterministic and identical to NetworkX's power iteration, but it is one valid answer among many.
- **NetworkX versions:** this tool reproduces `nx.hits` as it is in NetworkX 3.7, where the default is `method="power_iteration"`. Older 3.x releases computed `nx.hits` with SciPy's `svds` instead. Where the top eigenvalue is well separated (karate, lesmis, courses, airports), both methods give the same scores. Where it is repeated (`projects`), `svds` may return a different, equally valid vector. With `normalized=false`, `svds` also returns unit-length vectors rather than max = 1.
- Nodes with no incoming (or no outgoing) edges get authority (or hub) score 0.

## Errors
| Situation | Response |
| --- | --- |
| Unknown `graph_id` | error, suggesting `list_graphs` |
| Graph with no edges (or no nodes) | error: HITS needs at least one edge |
| `score` not hub/authority/both | error listing the valid values |
| `top_k` outside 1–100, `max_iter` outside 1–100,000, `tol` not in (0, 1), non-boolean flags | error giving the valid range |
| Unknown parameter | error listing the accepted parameters |
| Negative/non-finite or all-zero weights | error suggesting `weighted=false` |
| Not converged within `max_iter` | `ok` with `converged: false` and a warning in the summary suggesting a larger `max_iter` |
