# reachability

**Author:** 92711a92 · **Tier:** easy · **Category:** paths

## What it computes
Runs a breadth-first search (BFS) from `source` and reports whether `target` is among the nodes it reaches. BFS also records each node's parent, so when the target is reachable the tool rebuilds the fewest-hop path. It also reports how many nodes the source can reach. Time O(V + E), memory O(V).

## When to use it
Whenever the question is whether *any* route exists, not which one is shortest by distance.
- "Can you fly from Chennai to Lisbon at all, with any number of changes?"
- "Is CS101 (directly or indirectly) a prerequisite of CS301?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| source | string | (required) | Start node id (use `lookup_node` to find it) |
| target | string | (required) | Node id to reach |
| ignore_direction | boolean | false | On a directed graph, treat edges as two-way |

## Output
`result` is an object, not a list:
```json
{"reachable": true,
 "source": {"id": "MAA", "label": "Chennai International Airport"},
 "target": {"id": "LIS", "label": "Humberto Delgado Airport (Lisbon Portela Airport)"},
 "hops": 2, "path": [{"id": "MAA", "label": "Chennai International Airport"},
                     {"id": "DXB", "label": "Dubai International Airport"},
                     {"id": "LIS", "label": "Humberto Delgado Airport (Lisbon Portela Airport)"}],
 "path_truncated": false, "nodes_reachable_from_source": 499}
```
If the target is unreachable, `reachable` is false, `hops` is null and `path` is empty: an unreachable target is a valid answer, not an error. A path longer than 50 nodes is shortened (first 49 nodes plus the target) and `path_truncated` is true. Does not return `result_graph_id`.

## Graphs it supports
Directed and undirected graphs. On a directed graph it follows edge direction (A→B does not mean B→A) unless `ignore_direction` is true. Weights are ignored; use `shortest_path_weighted` for the shortest distance.

## Errors
- Unknown `graph_id`: use `list_graphs`.
- `source` or `target` missing or not a node id: use `lookup_node`.
- `ignore_direction` is not true or false.
- Unknown extra parameter.
