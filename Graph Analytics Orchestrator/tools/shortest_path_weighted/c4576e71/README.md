# shortest_path_weighted

**Author:** c4576e71 · **Tier:** medium · **Category:** paths

## What it computes
The cheapest path between two nodes using Dijkstra's algorithm with a binary heap, O((V + E) log V). Neighbours are visited in node-id order, so ties give the same path every run. The search stops as soon as the target is settled.

## When to use it
- "What is the shortest route by distance from Chennai to Lisbon?"
- "How far apart are these two characters in the co-appearance network?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| source | string | (required) | Node id where the path starts |
| target | string | (required) | Node id where the path ends |

## Output
`result` has `source`, `target`, `distance` (rounded to 6 places), `hops` and `path`, a list of nodes (id, label, `distance_from_source`). If source and target are the same node, the distance is 0. No `result_graph_id`.

## Graphs it supports
Directed (edge direction is followed) and undirected graphs. Unweighted graphs count every edge as 1. Weights must be non-negative.

## Errors
- Unknown graph id, or missing `source` / `target`.
- A node that is not in the graph (the message points to `lookup_node`).
- No path between the nodes (for example against edge direction).
- A negative edge weight.
- Unknown extra parameter.
