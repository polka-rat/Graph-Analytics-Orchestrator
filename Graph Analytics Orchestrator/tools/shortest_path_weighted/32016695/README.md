# shortest_path_weighted

**Author:** 32016695 ([ANONYMOUS]) · **Tier:** medium · **Category:** paths

## What it computes
The path between two nodes with the lowest total edge weight, using Dijkstra's algorithm. Dijkstra keeps a priority queue (a binary heap) of nodes ordered by their best known distance from the source. It repeatedly settles the closest unsettled node and relaxes its outgoing edges, so when the target is settled its distance is final. Predecessor links are then followed back from the target to rebuild the path. The search stops as soon as the target is settled. Time complexity is O((V + E) log V).

Ties are deterministic: equal distances leave the heap in node-id order, and a node's predecessor changes only when a strictly shorter distance is found.

## When to use it
Questions about the cheapest, shortest or closest route when edges have a cost:
- "What is the shortest route by distance from Chennai to Lisbon?" Answer: MAA → DXB → LIS, 9,071 km.
- "How closely is Champtercier linked to Valjean in Les Misérables?" (the weights add up)

For the fewest *hops* rather than the least total weight, use `shortest_path_unweighted`.

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| source | string | (required) | Id of the start node (use `lookup_node` to find it) |
| target | string | (required) | Id of the end node (use `lookup_node` to find it) |
| ignore_direction | boolean | false | Directed graphs only: treat every edge as two-way. If a pair is joined both ways, the cheaper edge is used. |
| top_k | integer | (ignored) | Accepted so that orchestrators can pass it to every tool; a path has no top-k. |

## Input handling
LLMs don't always send clean values, so the tool accepts the unambiguous ones instead of failing:
- `ignore_direction` may arrive as `"true"`, `"false"`, `"yes"`, `"no"`, `1` or `0`. Anything else is an error.
- A node id in the wrong case (`maa` for `MAA`) or with spaces around it is accepted when it matches exactly one node.
- A missing `source` or `target` gives an error that says which parameter is missing.
- The tool also works on graphs registered by other tools (ids like `airports~3`).

## Output
```json
{
  "source": {"id": "MAA", "label": "Chennai International Airport"},
  "target": {"id": "LIS", "label": "Humberto Delgado Airport (Lisbon Portela Airport)"},
  "reachable": true, "distance": 9071.0, "hops": 2,
  "path": [
    {"id": "MAA", "label": "Chennai International Airport", "step_weight": null, "distance_so_far": 0.0},
    {"id": "DXB", "label": "Dubai International Airport", "step_weight": 2933.0, "distance_so_far": 2933.0},
    {"id": "LIS", "label": "Humberto Delgado Airport (Lisbon Portela Airport)", "step_weight": 6138.0, "distance_so_far": 9071.0}
  ],
  "path_truncated": false
}
```
- `step_weight` is the weight of the edge into that node, and `distance_so_far` is the running total. Numbers are rounded to 6 decimal places.
- If the target cannot be reached, `status` is still `ok`, with `reachable: false`, `distance: null` and an empty `path`. The summary says there is no path and, on directed graphs, suggests `ignore_direction=true`.
- If a path is too long for the 8 KB limit, nodes are removed from the middle and `path_truncated` is true. `distance` and `hops` stay exact.
- The tool does not return a subgraph: `result_graph_id` is always `null`.

## Graphs it supports
Directed and undirected, weighted or unweighted. Weights are treated as costs to add up: kilometres for `airports`, and shared chapters for `lesmis`. On unweighted graphs every edge counts 1, so the distance is the hop count. Negative weights are refused, because Dijkstra's algorithm is not correct with them.

## Errors
- Unknown `graph_id`: use `list_graphs`.
- Unknown `source` or `target`: use `lookup_node` to find the id.
- `ignore_direction` that is not true or false.
- The graph has a negative edge weight. The error names the edge.
- Any parameter not listed above.

## Tests
`tests/test_shortest_path_weighted.py` checks distances against NetworkX's `dijkstra_path_length` on 40 node pairs each in `airports` and `lesmis`, and on the undirected version of airports. It also checks that every returned path uses real edges and adds up to the reported distance. Small graphs built inside the tests cover a cheap long route beating an expensive direct edge, a negative weight, and a 300-edge path that must be shortened to fit 8 KB. The remaining tests cover unreachable targets, source equal to target, every error case, and that results are deterministic.
