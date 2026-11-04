# reachability

**Author:** 91f2b762 · **Tier:** easy · **Category:** paths

## What it computes
Whether a path exists from a source node to a target node. It runs a breadth-first search from the source, following edge direction, and stops as soon as the target is found. BFS visits nodes in order of hop count, so the same search also gives the fewest hops. Time complexity is O(V + E).

## When to use it
Yes/no questions about connectivity.
- "Can you get from Chennai to Lisbon at all?"
- "Does completing CS101 eventually lead to CS301 through prerequisites?"

For the actual route or its distance use a shortest-path tool instead.

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| source | string | (required) | Node id where the path starts |
| target | string | (required) | Node id where the path should end |

## Output
`result` is an object; `result_graph_id` is always `null`.

```json
{"source": {"id": "MAA", "label": "Chennai International Airport"},
 "target": {"id": "LIS", "label": "Humberto Delgado Airport (Lisbon Portela Airport)"},
 "reachable": true,
 "hops": 2}
```

`reachable` is `true` or `false`; `hops` is the fewest edges on a path, or `null` when there is none. A node is reachable from itself in 0 hops. "No path" is a normal answer (`status: ok`, `reachable: false`), not an error.

## Graphs it supports
Directed and undirected graphs, weighted or not (weights are ignored). On a directed graph the search follows edge direction, so reachable A to B does not imply reachable B to A.

## Errors
- Unknown `graph_id`: the error says to use `list_graphs`.
- `source` or `target` missing, or not a node of the graph: the error names the parameter and says to use `lookup_node`.
- Any unexpected extra parameter.
