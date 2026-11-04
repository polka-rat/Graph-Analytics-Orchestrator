# motif_count

**Author:** e1e14ad1 · **Tier:** hard · **Category:** structure

## What it computes
Counts of 3-node patterns. Each **triangle** (three nodes linked pairwise, direction ignored) is found exactly once from adjacency, as u < v < w with all three pairs linked, by intersecting neighbour sets: O(edges * max degree). Everything else follows from that:

- **open triads** = connected triples minus three per triangle, where connected triples = sum over nodes of C(degree, 2);
- on directed graphs a triangle is a **feed-forward loop** (a->b, b->c, a->c) or a **directed 3-cycle** (a->b, b->c, c->a) when all three of its pairs are one-way. A cycle has one outgoing edge per node inside the triple; a feed-forward loop does not. A triangle with any two-way pair is neither.

**Loops and cycles are induced:** three nodes joined by exactly those three one-way edges. This matters in `airports`, where 99% of links are two-way: the induced count is 1 feed-forward loop and 5 directed 3-cycles, while counting "contains the pattern" would give ~497,000 and ~166,000. Triangles ignore direction, so loops and cycles are among them.

An undirected graph counts as a directed one where every pair is two-way, so only triangles and open triads apply. Weights and self-loops are ignored.

## When to use it
- "How many triangles / feed-forward loops are in this network?"
- "Which small patterns are most common?"
- "Which nodes are in the most triangles?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| top_k | integer | 10 | How many nodes to list in `top_nodes` (1 to 100). Counts are never truncated |

## Output
`result`: `triangles`, `open_triads`, `feed_forward_loops` and `directed_cycles` (the last two are `null` on undirected graphs), and `top_nodes`: `{id, label, triangles}` for the nodes in the most triangles (a triangle counts for each of its three nodes), ties by id. The list is shortened if long labels would exceed 8 KB. `result_graph_id` is `null`.

## Graphs it supports
Directed and undirected, weighted or not. Graphs with fewer than 3 nodes or no edges are valid: all counts are 0.

## Errors
- Unknown graph.
- `top_k` not a whole number from 1 to 100.
- Unknown parameter names.

A graph with no triangles (for example `projects`, which is bipartite) is **not** an error: counts are 0 and `top_nodes` is empty.
