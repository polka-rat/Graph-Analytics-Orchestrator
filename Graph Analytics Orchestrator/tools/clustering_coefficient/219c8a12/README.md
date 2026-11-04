# clustering_coefficient

**Author:** 219c8a12 · **Tier:** easy · **Category:** structure

## What it computes
The **local clustering coefficient** of a node v is the fraction of pairs of v's neighbours that are themselves connected:

C(v) = 2·T(v) / (k(v)·(k(v) − 1))

Here T(v) is the number of triangles through v and k(v) is the number of distinct neighbours. **If k(v) < 2, C(v) = 0**, because no pair of neighbours exists.

Every call also reports two graph-wide numbers in the summary:
- **Average clustering:** the mean of C(v) over **all** nodes, with degree-<2 nodes counted as 0 (the NetworkX `average_clustering` convention).
- **Global transitivity:** 3 × triangles / connected triples. This is a different measure from the average: it weights high-degree nodes more.

**Algorithm.**
1. Build simple undirected neighbour sets.
2. Rank nodes by (degree, index) and orient each edge from the lower-ranked endpoint to the higher-ranked one.
3. For each oriented edge (u, v), intersect the forward sets of u and v. Each triangle is found exactly once, and each of its three corners is credited.

The time is O(m·√m) on sparse graphs and the memory is O(n + m). On `airports` (500 nodes, 10,126 undirected edges) a call takes well under a second.

## When to use it
Use it for questions about how tightly knit a neighbourhood is:
- "How tightly knit is the instructor's circle of friends?" → `{"graph_id": "karate", "node": "m1"}`
- "Which characters sit in the densest clusters?" → `{"graph_id": "lesmis", "top_k": 5, "min_degree": 4}`

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph (a dataset or a subgraph id such as `karate~1` from `filter_nodes`) |
| node | string | none | A node id. If given, returns only that node's coefficient (the graph numbers are still in the summary) |
| top_k | integer | 10 | When no node is given, how many of the most clustered nodes to return (1 to 100) |
| min_degree | integer | 2 | When ranking, only nodes with at least this many neighbours are listed. It does **not** change the average. Raise it to skip trivial 1.0 scores of degree-2 nodes |

## Output
`result` is a list of nodes, each `{"id", "label", "score", "degree", "triangles"}`:
- `score` is C(v), rounded to 6 decimals.
- `degree` is the number of distinct neighbours, ignoring direction.
- `triangles` is T(v).

With `node`, the list has that one node. Without it, the list holds the top_k nodes sorted by score (descending, compared after rounding to 6 decimals), with ties broken by node id (ascending). If the list would push the response over 8 KB, it is shortened and the summary says so. `result_graph_id` is always `null`.

```json
{"status": "ok",
 "result": [{"id": "m1", "label": "Member 1 (instructor)", "score": 0.15, "degree": 16, "triangles": 18}],
 "summary": "Member 1 (instructor) (m1) has clustering coefficient 0.15: 18 of the 120 pairs among its 16 neighbours are connected to each other. The graph average is 0.570638 over all 34 nodes (nodes with fewer than 2 neighbours count as 0) and global transitivity is 0.255682.",
 "result_graph_id": null, "error": null}
```

## Graphs it supports
- **Undirected:** the natural case.
- **Directed:** direction is ignored. u and v are neighbours if either edge u→v or v→u exists, and a reciprocal pair counts once. The summary says so.
- **Weighted:** weights are ignored (unweighted clustering, as in `nx.clustering` with its default `weight=None`). The summary says so.
- **Self-loops** are ignored. Duplicate edges are counted once.
- **Disconnected graphs** work normally, because clustering is local.

## Errors
| Situation | Response |
| --- | --- |
| Unknown `graph_id` | error, suggesting `list_graphs` |
| Unknown `node` (e.g. a name instead of an id) | error, suggesting `lookup_node` |
| `top_k` not a whole number from 1 to 100 | error giving the valid range |
| `min_degree` negative or not a whole number | error giving the valid values |
| Unknown parameter | error listing the accepted parameters |
| Graph with no nodes | error suggesting another graph |
| Graph with no edges (ranking) | error: every coefficient is 0, nothing to rank; pick a graph with edges. Asking for one `node` still returns its score of 0 |
| No node reaches `min_degree` | error: nothing to rank; lower `min_degree` |
| Node with fewer than 2 neighbours | `ok`, score 0, summary explains why |
