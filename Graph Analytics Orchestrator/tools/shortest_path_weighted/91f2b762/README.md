# shortest_path_weighted

**Author:** 91f2b762 · **Tier:** medium · **Category:** paths

## What it computes
The cheapest path between two nodes, where the cost of a path is the sum of its edge weights. It uses Dijkstra's algorithm with a binary heap (`heapq`), stopping as soon as the target is settled. Time complexity is O((V + E) log V). Ties are settled in node-id order, so the answer is deterministic.

## When to use it
Questions about the best route by distance or cost.
- "What is the shortest route by distance from Chennai to Lisbon?"
- "What is the cheapest chain of links between two characters, if each link costs its edge weight?"

For a plain yes/no answer use `reachability`.

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| source | string | (required) | Node id where the route starts |
| target | string | (required) | Node id where the route ends |

## Output
`result` is an object; `result_graph_id` is always `null`.

```json
{"source": {"id": "MAA", "label": "Chennai International Airport"},
 "target": {"id": "LIS", "label": "Humberto Delgado Airport (Lisbon Portela Airport)"},
 "distance": 9071.0,
 "hops": 2,
 "path": [{"id": "MAA", "label": "Chennai International Airport"}, {"id": "DXB", "label": "Dubai International Airport"}, {"id": "LIS", "label": "Humberto Delgado Airport (Lisbon Portela Airport)"}]}
```

`distance` is the total weight (km in `airports`) rounded to 6 decimals and `hops` the number of edges. A path longer than 40 nodes is shortened to its first and last 20 nodes and flagged with `"path_truncated": true`, to stay under the 8 KB output limit.

## Graphs it supports
Directed graphs (edge direction is followed) and undirected graphs, weighted or not. On an unweighted graph every edge costs 1, so the result is the fewest-hop path. Weights must be non-negative.

## Errors
- Unknown `graph_id`: use `list_graphs`.
- `source` or `target` missing, or not a node of the graph: the error names the parameter and says to use `lookup_node`.
- No path between the two nodes (disconnected graph, or wrong direction): the error says so and suggests `reachability`.
- A negative edge weight in the graph (none of the provided datasets has one).
- Any unexpected extra parameter.
