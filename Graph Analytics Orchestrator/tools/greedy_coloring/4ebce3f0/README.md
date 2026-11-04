# greedy_coloring

**Author:** 4ebce3f0 · **Tier:** medium · **Category:** structure

## What it computes
A proper colouring of the nodes: no two nodes joined by an edge get the same colour. The nodes are put in an order chosen by `strategy`, then each node gets the smallest colour (0, 1, 2, ...) not used by its already-coloured neighbours. The number of colours is an upper bound on the chromatic number (the true minimum) and never more than the maximum degree + 1.

Strategies:
- `largest_first` (default): highest degree first. O(V log V + E).
- `dsatur`: next is the uncoloured node with the most distinct colours among its neighbours, ties by degree. Often uses fewer colours. O(V² + E).
- `smallest_last`: repeatedly remove a node of smallest remaining degree, then colour in reverse removal order. O(V² + E).

Ties keep the graph's node order, as NetworkX does, so `largest_first` and `dsatur` give exactly NetworkX's `greedy_color` result. `smallest_last` breaks ties by node id.

## When to use it
Scheduling and conflict questions where linked nodes must be kept apart. Examples:
- "How many exam slots are needed so no two clashing exams share a slot?"
- "Split the Les Misérables characters into groups with no two co-appearing characters in the same group."

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| strategy | string | largest_first | `largest_first`, `dsatur` or `smallest_last` |
| top_k | integer | 10 | How many member nodes to list per colour class (1 to 100) |
| node | string | none | Optional node id; the result then gives its colour |

## Output
`result` is an object:
- `num_colors`, `strategy`, `valid` (always true: the colouring is checked before returning), `max_degree`
- `color_classes`: one entry per colour, each with `color`, `size`, `members` (up to `top_k` nodes as `{id, label}`, sorted by id) and `members_shown`
- `node` (only if `node` was given): `{id, label, color}`

Example (`graph_id="karate"`): 5 colours with class sizes 4, 11, 14, 3, 2.

`result_graph_id` is always null. If the output would pass 8 KB, fewer members are listed per class; the sizes are always complete.

## Graphs it supports
Undirected graphs, weighted or not (weights are ignored). Directed graphs are accepted with edge direction ignored, since a conflict goes both ways. Self-loops are ignored.

## Errors
- Unknown `graph_id`: use `list_graphs`.
- Unknown parameter, or a `strategy` that is not one of the three.
- `top_k` not a whole number from 1 to 100.
- `node` not in the graph: use `lookup_node`.
- The graph has no nodes.