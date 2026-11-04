# bipartite_check

**Author:** 62a230f4 · **Tier:** medium · **Category:** structure

## What it computes
A 2-colouring (BFS from each uncoloured node) of the undirected view of the graph. Time is O(n + m). The graph is bipartite if and only if there is no self-loop and no odd cycle.

## When to use it
Questions about splitting nodes into two groups with no internal links.
- Can this network be split into two independent sets?
- What are the two sides of the student–project graph?

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| top_k | integer | 10 | How many nodes to list from each side (1 to 100) |

## Output
If bipartite: `result.is_bipartite` is true, `left` and `right` each have `size`, `nodes` (up to top_k, sorted by id), and `graph_id` of a registered subgraph of that whole side. `result_graph_id` is the larger side (ties go to left).
If not: `is_bipartite` is false, with a `reason` and an adjacent same-colour pair when the obstruction is an odd cycle. `result_graph_id` is null.

## Graphs it supports
Undirected and directed (direction is ignored). Weighted edges are treated as unweighted.

## Errors
- Unknown `graph_id`: use `list_graphs`.
- `top_k` outside 1..100.
- Extra parameters.
