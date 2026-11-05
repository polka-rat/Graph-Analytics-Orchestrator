# label_propagation

**Author:** 6ae0e02c · **Tier:** medium · **Category:** community

## What it computes
Label propagation for community detection. Every node starts with its own label; then, in a seeded random order, each node adopts the most common label among its neighbours (ties go to the smallest label id). A pass that changes nothing ends the algorithm, or `max_iter` passes at most. Nodes that end up sharing a label form one community. The partition is scored with Newman modularity, $Q = \sum_c [L_c/m - (D_c/2m)^2]$, where $L_c$ counts edges inside community $c$, $D_c$ is the sum of degrees inside it and $m$ is the number of edges. Cost is $O(\text{max\_iter} \cdot m)$ with hash-map counting, so it is near-linear in the number of edges.

## When to use it
- "What groups exist among these airports?" (`airports`)
- "Which characters in Les Misérables cluster together?" (`lesmis`)

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| top_k | integer | 10 | How many of the largest communities to return (1 to 100) |
| seed | integer | 0 | Seed for the node visit order; the same seed reproduces the same partition |
| max_iter | integer | 100 | Maximum number of propagation passes (1 to 1000) |

## Output
`result` = `{"num_communities": int, "modularity": float, "communities": [{"community", "size", "graph_id", "members_shown", "truncated", "nodes"}]}`. Communities are sorted by size descending, ties by the smallest member id. `num_communities` counts **all** communities found, not just those returned. Each **returned** community is registered as a subgraph and its id appears as `graph_id`; `result_graph_id` is the largest community's id. Floats are rounded to 6 places.

If a community is too large to list in full within the 8 KB output limit, `nodes` shows the first `members_shown` members and `truncated` is `true`; the full membership is always available through that community's `graph_id`. If there are more communities than fit, the smallest are dropped and the summary says so. Only the communities that are returned get a `graph_id`, because registering a subgraph copies the parent's edges.

## Graphs it supports
Undirected and directed. On a directed graph the edge directions are ignored (neighbours are taken from `undirected_neighbors`) and the summary says so. Weights are ignored. Self-loops are removed, so a node never votes for itself.

## Errors
- Unknown `graph_id`, or a `graph_id` that is not a string.
- `top_k` is not a whole number from 1 to 100 (booleans are rejected).
- `seed` is not a whole number.
- `max_iter` is not a whole number from 1 to 1000.
- Any unknown parameter name.
- A graph with no nodes.
