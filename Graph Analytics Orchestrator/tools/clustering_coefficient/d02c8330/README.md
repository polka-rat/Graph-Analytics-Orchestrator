# clustering_coefficient (d02c8330)

**Answers:** "How tightly knit is Alice's circle?", "Do X's friends know each other?", "How clustered is this network?"

## Algorithm
For each node `v` with degree `d`, count links among its neighbours `T(v)` via set intersections
(`sum |N(u) ∩ N(v)| / 2` over neighbours `u`). Local clustering is `2·T(v) / (d·(d−1))`, or 0 when `d < 2`.
The graph average is the mean over all nodes (zeros included, as in NetworkX `average_clustering`).
Transitivity is `3·triangles / connected triples`. Cost: O(Σ deg²) time, which takes well under a second on `airports`.

## Parameters
| name | type | default | meaning |
|---|---|---|---|
| graph_id | string | required | graph to analyse |
| node | string | none | node whose local clustering you want |
| top_k | int | 10 | number of most-clustered nodes to list (1–100) |

## Output
`average_clustering`, `transitivity`, `triangles`, `nodes`, plus either `node` (with `clustering`,
`triangles`, `degree`) or `top_nodes` (sorted by clustering desc, ties by id asc). Floats rounded to 6 dp.

## Edge cases
Directed graphs: direction is ignored (the summary says so). Weights are ignored, self-loops skipped.
Unknown graph, unknown node, bad `top_k`, unknown parameters and empty graphs return a clear error.

## Example
`python run_tool.py registry/tools/clustering_coefficient/d02c8330 graph_id=karate node=m1`
gives clustering 0.15 (18 of 120 neighbour pairs linked) and a graph average of 0.570638.
