# max_flow_min_cut

**Author:** 1e59ba80 · **Tier:** hard · **Category:** paths

## What it computes
The maximum flow from a source node to a sink node, using the Edmonds–Karp algorithm, and the minimum cut that limits it.

- **Maximum flow:** Edmonds–Karp repeatedly finds the shortest augmenting path in the residual graph by breadth-first search and pushes the path's bottleneck capacity along it, until the sink is unreachable.
- **Minimum cut:** the sink side is every node that can still reach the sink through residual capacity, and the source side is everything else. This is the same cut NetworkX's `minimum_cut` returns. The cut edges are the edges going from the source side to the sink side, and their total capacity equals the maximum flow.

Time complexity is O(V · E²).

## When to use it
Bottleneck, capacity and separation questions between two nodes. For example:
- "Where is the bottleneck between Chennai and Lisbon?"
- "Which friendships would have to break to separate the instructor (m1) from the administrator (m34)?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| source | string | (required) | Node id the flow starts from |
| sink | string | (required) | Node id the flow ends at; must differ from `source` |
| capacity | string | `"weight"` | `"weight"`, `"unit"` (every edge has capacity 1, so the cut counts edges), or a numeric edge attribute such as `"airlines"` |

On airports, `weight` is the distance in km. `capacity="airlines"` (the number of airlines on a route) is usually the more meaningful capacity.

## Output
`result` is an object:
- `source` and `sink` (node refs) and `capacity`
- `max_flow` and `cut_capacity`, which are equal
- `num_cut_edges`, `source_side_size`, `sink_side_size` and `augmenting_paths`
- `cut_edges`: each has `from` (source side), `to` (sink side) and `capacity`, sorted by capacity (largest first), then by node id
- `cut_edges_shown`

```json
{"source": {"id": "CS101", "label": "Programming Basics"}, "sink": {"id": "CS405", "label": "Network Science"},
 "capacity": "weight", "max_flow": 1.0, "cut_capacity": 1.0, "num_cut_edges": 1,
 "source_side_size": 17, "sink_side_size": 4, "augmenting_paths": 1,
 "cut_edges": [{"from": {"id": "CS306", "label": "..."}, "to": {"id": "CS405", "label": "Network Science"},
                "capacity": 1.0}],
 "cut_edges_shown": 1}
```

A maximum flow of 0 means there is no path from source to sink; the cut list is then empty. Floats are rounded to 6 decimal places. It does not return `result_graph_id`.

If the output would exceed 8 KB, only the largest cut edges are listed and the summary says so. For example, ATL → FRA with `capacity="unit"` has 117 cut edges, and 38 are listed.

## Graphs it supports
- **Directed graphs.**
- **Undirected graphs:** each edge carries flow in both directions, up to its capacity.
- **Weighted and unweighted graphs:** unweighted graphs have weight 1, so `weight` and `unit` give the same result there.

## Errors
- Unknown `graph_id`: use `list_graphs`.
- Unknown parameter.
- Missing or unknown `source` or `sink`: use `lookup_node`.
- `source` equal to `sink`.
- A `capacity` that is not `"weight"`, `"unit"` or a numeric edge attribute of the graph.
- A negative capacity.
