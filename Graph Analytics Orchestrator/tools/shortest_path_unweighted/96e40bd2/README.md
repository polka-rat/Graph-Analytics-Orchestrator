# shortest_path_unweighted

**Author:** 96e40bd2 · **Tier:** easy · **Category:** paths

## What it computes
The path with the fewest hops (edges) between a source node and a target node, found with breadth-first search (BFS). Edge weights are ignored: every edge is one hop. Time O(V + E), memory O(V).

## When to use it
Questions about the fewest steps between two nodes. Examples:
- "What is the fewest number of flights from Chennai to Lisbon?" (graph `airports`, source `MAA`, target `LIS`)
- "How many hops separate member 1 and member 34 in the karate club?"

Use `shortest_path_weighted` instead when the question is about distance or cost.

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| source | string | (required) | Node ID where the path starts |
| target | string | (required) | Node ID where the path ends |

## Output
`result` is the ordered list of nodes on the path, each `{"id", "label", "step"}` (step 0 is the source). The hop count is `len(result) - 1` and is stated in `summary`. `result_graph_id` is `null`.
```json
{"status": "ok",
 "result": [{"id": "MAA", "label": "Chennai International Airport", "step": 0},
            {"id": "DXB", "label": "Dubai International Airport", "step": 1},
            {"id": "LIS", "label": "Humberto Delgado Airport (Lisbon Portela Airport)", "step": 2}],
 "summary": "The fewest hops from Chennai International Airport to ... is 2: ...",
 "result_graph_id": null, "error": null}
```
If several paths have the same length, the tool returns one deterministically (neighbours are explored in ascending node-id order). A path longer than the 8 KB output limit allows is shortened to its first and last 30 nodes (stated in the summary).

## Graphs it supports
Directed and undirected graphs, weighted or not. On directed graphs the path follows edge direction (so A to B can exist while B to A does not).

## Errors
- Unknown graph: tells you to use `list_graphs`.
- Unknown or missing `source` / `target`: tells you to use `lookup_node`.
- No path between the two nodes (different components, or wrong direction): says so and suggests swapping them.
- Unknown parameter: lists the accepted parameters.
