# max_flow_min_cut

**Author:** 32016695 ([ANONYMOUS]) · **Tier:** hard · **Category:** paths

## What it computes
The **maximum flow** from a source node to a sink node, and a **minimum cut** separating them, using the Edmonds–Karp algorithm.

1. Build a residual network. Each edge `u→v` with capacity `c` becomes an arc with residual capacity `c` plus a reverse arc starting at 0. The reverse arc lets later paths undo flow sent earlier. For an undirected edge, both arcs start at `c`, because flow may go either way.
2. Repeatedly find a **shortest** augmenting path (fewest arcs) from source to sink by breadth-first search over arcs with spare capacity. Push the path's bottleneck (its smallest residual capacity) along it: subtract it on each arc and add it to the reverse arc.
3. When no augmenting path is left, the flow is maximum. The nodes still reachable from the source in the residual network form the source side `S` of a minimum cut. The original edges leaving `S` are the cut edges. By the max-flow min-cut theorem, their total capacity equals the maximum flow, and the tool reports both values so they can be compared.

Choosing shortest paths bounds the number of augmentations by O(VE), so the running time is O(VE²) regardless of the capacity values. Arcs are stored in flat lists where arc `i ^ 1` is the reverse of arc `i`, and nodes are processed in id order, so results are deterministic.

## When to use it
- "Where is the bottleneck between Chennai and Lisbon?" (`capacity="airlines"`)
- "How many friendships must break before the instructor's and the administrator's groups are fully separated?" (karate, `capacity="unit"`)
- "How many edge-disjoint routes connect A and B?" (`capacity="unit"`)

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| source | string | (required) | Id of the node the flow starts from |
| sink | string | (required) | Id of the node the flow ends at (must differ from source) |
| capacity | string | `"weight"` | `weight` uses the edge weight (1 on unweighted graphs). `unit` gives every edge capacity 1, so the answer counts edge-disjoint paths. Any other value names a numeric edge attribute, e.g. `airlines` in airports. |
| top_k | integer | 10 | How many cut edges to list, largest capacity first (1 to 100) |

## Output
```json
{
  "source": {"id": "MAA", "label": "Chennai International Airport"},
  "sink": {"id": "LIS", "label": "Humberto Delgado Airport (Lisbon Portela Airport)"},
  "capacity": "airlines", "max_flow": 73.0, "augmenting_paths": 52,
  "cut_size": 28, "cut_capacity": 73.0,
  "source_side_size": 1, "sink_side_size": 499,
  "cut_edges": [
    {"source": {"id": "MAA", "label": "Chennai International Airport"},
     "target": {"id": "BOM", "label": "Chhatrapati Shivaji International Airport"}, "capacity": 7.0}, ...
  ],
  "cut_edges_truncated": true
}
```
- `max_flow` and `cut_capacity` are always equal (max-flow min-cut theorem).
- `cut_size`, `cut_capacity` and the side sizes cover the whole cut. `cut_edges` lists at most `top_k` edges, sorted by capacity (largest first) and then by node ids. If long labels would push the response over 8 KB, the list is shortened further. `cut_edges_truncated` says whether anything was left out.
- If the sink cannot be reached, `status` is still `ok` with `max_flow` 0 and no cut edges, and the summary explains why.
- The tool does not return a subgraph: `result_graph_id` is always `null`.

## Input handling
LLMs don't always send clean values, so the tool accepts the unambiguous ones instead of failing:
- `top_k` may arrive as `3.0` or `"3"`; it is read as a whole number. `2.5` or `"lots"` is still an error.
- A node id in the wrong case (`M1` for `m1`) or with spaces around it is accepted when it matches exactly one node.
- `capacity` is case-insensitive (`Airlines` works). An unknown attribute name gives an error that lists the attributes the graph really has.
- A missing `source` or `sink` gives an error that says which parameter is missing.
- The tool also works on graphs registered by other tools (ids like `airports~3`); edge attributes such as `airlines` are carried into subgraphs.

## Graphs it supports
Directed graphs, where flow follows edge direction and edges in both directions are separate arcs. Undirected graphs, where each edge carries flow either way, up to its capacity. Weighted or unweighted. For `airports`, use `capacity="airlines"`: the default weight is distance in km, which is not a capacity.

## Errors
- Unknown `graph_id`: use `list_graphs`.
- Unknown `source` or `sink`: use `lookup_node` to find the id.
- `source` and `sink` are the same node.
- `capacity` names an attribute that the edges don't have, or that isn't numeric.
- A negative capacity. The error names the edge.
- `top_k` not a whole number from 1 to 100.
- Any parameter not listed above.

## Tests
`tests/test_max_flow_min_cut.py` checks the flow value against NetworkX's `maximum_flow_value` on 12 node pairs in each of karate, lesmis, airports (`airlines`), courses (`unit`) and projects. For each complete cut it checks that the capacities add up to the flow and that removing the cut edges really disconnects source from sink. With `unit` capacities it checks the count against `local_edge_connectivity`. Small graphs built inside the tests cover the CLRS textbook network (flow 23, with its known cut) and edges running both ways between two nodes. The remaining tests cover zero flow, the 8 KB limit and `top_k` ordering, speed on the two biggest hubs, a negative capacity, every error case, and that results are deterministic.
