# connected_components

**Author:** f9857550 (Cheripelly Karthik) · **Tier:** easy · **Category:** community

## What it computes
Breadth-first search from every not-yet-visited node (in node-id order) labels each node with its component. Components are sorted largest first (ties: smallest node id). Each returned component is registered with the store as a subgraph. Time O(V + E).

## When to use it
Questions about whether a network hangs together and how it falls into separate pieces:
- "Is the karate club network connected?"
- "What is the largest connected part of the airport network, and how many airports are cut off?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| top_k | integer | 10 | How many components to return, largest first (1 to 100) |

## Output
`result` is a list of components:
```json
[{"rank": 1, "size": 34, "fraction_of_nodes": 1.0, "graph_id": "karate~1",
  "members": [{"id": "m1", "label": "Mr Hi"}, "..."], "members_truncated": true}]
```
At most 10 members are listed per component (to stay under 8 KB); the full set is in the subgraph `graph_id`. `result_graph_id` is the largest component, so other tools can run on it next.

## Graphs it supports
Undirected graphs (connected components). Directed graphs: edge direction is ignored, giving weakly connected components, and the summary says so and points to `strongly_connected_components`. Weights are ignored.

## Errors
- Unknown `graph_id` → use `list_graphs`.
- `top_k` not a whole number from 1 to 100.
- Unknown extra parameter.
- A graph with no nodes.
