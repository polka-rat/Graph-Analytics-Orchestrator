# topological_sort

**Author:** efd53284 · **Tier:** medium · **Category:** paths

## What it computes
For a directed acyclic graph, a topological order using Kahn's algorithm with a
min-heap. The heap returns the lexicographically smallest valid order, so the
output is deterministic.

If the graph contains a directed cycle, the tool returns one cycle instead:
a list of nodes `v0, v1, ..., vk` where every consecutive pair is an edge and
the last node has an edge back to `v0`. The cycle is found with an iterative
depth-first search.

Complexity: O((V + E) log V) for the ordering and O(V + E) for cycle detection.

## When to use it
Ordering and dependency questions:
- "In what order I need to do tasks or excute the nodes?"
- "Which courses must be completed before CS301?"
- "Does this dependency graph contain a cycle?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the directed graph |

## Output
For a DAG, `result` is a list of node references with a 1-based `position`, in
topological order. `result_graph_id` is always `null`. This is a complete
order, not a top-k list: every node appears exactly once, so `top_k` does not
apply.

For a cyclic graph, `result` is a list of node references with a 1-based
`position` and `"cycle": true`. The listed edges `v0→v1`, `v1→v2`, ...,
`vk→v0` form the cycle. The summary also prints the cycle path.

## Graphs it supports
Directed graphs, weighted or unweighted (weights are ignored). Disconnected
DAGs are supported: each component is ordered. `courses` is acyclic and returns
an order; `airports` contains cycles and returns one cycle. Undirected graphs
return an error because a topological order is defined only for directed
graphs.

## Errors
- Unknown `graph_id`.
- Undirected graph.
- A graph with no nodes.
- Unknown parameters (the tool accepts only `graph_id`).
