# articulation_points_bridges

**Author:** 3237bc9e · **Tier:** medium · **Category:** structure

## What it computes
Articulation points (nodes whose removal splits a component) and bridges (edges whose removal does the same), using Tarjan's low-link depth-first search. A child `c` of `u` with `low[c] >= disc[u]` makes `u` an articulation point (the root needs two or more children); a tree edge `u-c` with `low[c] > disc[u]` is a bridge. Time O(n + m).

## When to use it
Single points of failure in a network.
- "Which single airport closure would split the network?"
- "Who is the only link between two groups of characters?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| top_k | integer | 10 | How many articulation points and bridges to list (1 to 100) |

## Output
`articulation_point_count`, `bridge_count`, and up to `top_k` `articulation_points` and `bridges` (each bridge is a pair of nodes), sorted by node id. No `result_graph_id`.

```json
{"articulation_point_count": 1, "bridge_count": 1,
 "articulation_points": [{"id": "m1", "label": "Member 1 (instructor)"}],
 "bridges": [[{"id": "m1", "label": "Member 1 (instructor)"}, {"id": "m12", "label": "Member 12"}]]}
```

## Graphs it supports
Undirected graphs; directed graphs with edge direction ignored. Weights are ignored. Disconnected graphs are handled component by component.

## Errors
Unknown `graph_id`; `top_k` not a whole number from 1 to 100; unknown parameters.
