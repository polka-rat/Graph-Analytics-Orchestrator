# shortest_path_unweighted

**Author:** edba08e8 · **Tier:** easy · **Category:** paths

## What it computes
The fewest-hop path between two nodes, found with breadth-first search. Edge weights are ignored. Time O(V + E).
Neighbours are visited in sorted id order, so when several shortest paths exist the same one is always returned.

## When to use it
- "What is the fewest number of flights from Chennai to Lisbon?"
- "Can Member 1 reach Member 34, and through whom?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| source | string | (required) | Node id where the path starts |
| target | string | (required) | Node id where the path ends |

## Output
`result` is `{"reachable": true, "hops": 2, "source": {id,label}, "target": {id,label}, "path": [{id,label}, ...]}`.
If the target cannot be reached the tool returns `status: "error"` with a message saying no path exists and how to fix the call.
Paths longer than 60 nodes are shortened in the middle and flagged with `path_truncated`; `hops` is always exact.
`result_graph_id` is `null`.

## Graphs it supports
Directed and undirected, weighted or not (weights are ignored). On directed graphs edges are followed forward only.

## Errors
- No path from `source` to `target` (disconnected graph, or wrong direction in a directed graph).
- Unknown graph id, unknown `source` or `target` node (suggests `lookup_node`).
- Missing `source` or `target`.
- Unknown extra parameters.
- `source == target` is not an error: 0 hops, path of one node.
