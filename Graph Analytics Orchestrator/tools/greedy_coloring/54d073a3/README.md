# greedy_coloring

**Author:** 54d073a3 · **Tier:** medium · **Category:** structure

## What it computes
A greedy vertex colouring: nodes are processed one at a time in a fixed order, and each gets the smallest colour (0, 1, 2, ...) not already used by one of its neighbours. Adjacent nodes therefore never share a colour. The number of colours used is an upper bound on the chromatic number, and never exceeds $\Delta + 1$ where $\Delta$ is the maximum degree.

Two orderings are available through `strategy`:
- `largest_first` (default, Welsh-Powell): highest degree first; ties broken by node id (ascending). Gives the same colouring as NetworkX's `greedy_color(G, "largest_first")` on all provided datasets.
- `dsatur` (Brelaz): always colour the node with the most differently coloured neighbours next; ties by higher degree, then smaller node id. It is exact on bipartite graphs.

Time: $O(n + m)$ for `largest_first` (plus sorting), $O(n^2 + m)$ for `dsatur`.

## When to use it
- "How many exam slots avoid all clashes?" (nodes = exams, edges = shared students)
- "Into how many groups can the nodes be split so that no connected pair is in the same group?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| top_k | integer | 10 | How many nodes to list with their colour (1 to 100) |
| strategy | string | "largest_first" | "largest_first" or "dsatur" |

## Output
`result` is an object:
- `num_colors`: number of colours used.
- `strategy`, `num_nodes`, `max_degree`.
- `is_proper_coloring`: always `true` (checked by the tool before returning).
- `color_class_sizes`: list of `{color, size}`, one per colour.
- `nodes`: the first `top_k` nodes in colouring order, each `{id, label, color, degree}`.

The full colouring of a large graph does not fit the 8 KB response limit, so only `top_k` nodes are listed (fewer if the size limit requires it; the summary says how many). It does not return `result_graph_id`.

## Graphs it supports
Directed and undirected, weighted and unweighted. Direction and weights are ignored (neighbours in either direction count as adjacent). Self-loops are skipped. Isolated nodes get colour 0.

## Errors
- Unknown `graph_id`.
- `top_k` not a whole number from 1 to 100.
- `strategy` not one of the two names.
- Unknown parameter.
- A graph with no nodes.
