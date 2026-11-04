# connected_components

**Author:** 1e59ba80 · **Tier:** easy · **Category:** community and structure

## What it computes
Splits an undirected graph into its connected components (maximal groups of nodes in which every pair is joined by some path) and reports their sizes. It runs a breadth-first search from each unvisited node, in node-id order, and collects every node it reaches. Time complexity is O(V + E).

## When to use it
Questions about whether a network holds together and how it splits into separate parts. For example:
- "What is the largest connected part of the projects graph?"
- "Is the karate club network connected, or are some members cut off?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of an undirected graph |

## Output
`result` is an object:
- `num_components`, `is_connected`, `largest_size`, `num_isolated_nodes`
- `components`, largest first, with ties broken by smallest node id. Each has `rank`, `size`, `graph_id` (its registered subgraph), `members` (node refs sorted by id, at most 20) and `members_shown`.

```json
{"num_components": 2, "is_connected": false, "largest_size": 25, "num_isolated_nodes": 1,
 "components": [{"rank": 1, "size": 25, "graph_id": "projects~1",
                 "members": [{"id": "P01", "label": "Project 01"}, "..."], "members_shown": 20},
                {"rank": 2, "size": 1, "graph_id": "projects~2",
                 "members": [{"id": "...", "label": "..."}], "members_shown": 1}]}
```

Each listed component is registered with the store, and `result_graph_id` is the largest one, so another tool can run on it next.

If the output would exceed 8 KB, fewer members are listed per component (20, 10, 5, then none, keeping sizes and subgraph ids). As a last resort the smallest components are left out of the list, and the summary says so. The counts always cover every component.

## Graphs it supports
- **Undirected graphs:** weighted or unweighted; weights are ignored.
- **Directed graphs:** return an error that points to `strongly_connected_components`.

## Errors
- Unknown `graph_id`: use `list_graphs`.
- Any parameter other than `graph_id`.
- A directed graph.
- A graph with no nodes.
