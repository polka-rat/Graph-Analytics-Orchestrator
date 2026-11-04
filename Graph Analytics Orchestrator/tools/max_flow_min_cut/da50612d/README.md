# max_flow_min_cut

**Author:** da50612d · **Tier:** hard · **Category:** paths

## What it computes
The maximum amount that can flow from a `source` node to a `sink` node when every edge carries at most its capacity, and a minimum cut: the cheapest set of edges whose removal separates the sink from the source. By the max-flow min-cut theorem the two numbers are equal, so the cut edges are exactly the bottleneck.

**Edmonds–Karp:** the residual network is stored as flat arc lists (arc `a` and arc `a ^ 1` are each other's reverse). The algorithm repeatedly finds a shortest augmenting path (fewest edges) by breadth-first search, stopping as soon as the sink is reached, then pushes the path's bottleneck capacity along it and updates the residual capacities. When no augmenting path remains, the flow is maximum. The sink side of the cut is the set of nodes that can still reach the sink in the residual network; every other node is on the source side. This is the same partition `networkx.minimum_cut` returns. Time O(V·E²) in the worst case; on `airports` (500 nodes, 20 058 edges) the worst pair of hubs takes about 0.25 s.

Directed edges carry flow only in their direction. An undirected edge can carry flow either way, up to its capacity, as in `networkx.maximum_flow`.

## When to use it
Questions about capacity, bottlenecks and separating two nodes:
- "Where is the bottleneck between Chennai and Lisbon if each route carries as many units as it has airlines?"
- "How many edge-disjoint paths connect the instructor and the administrator in the karate club?" (`capacity="unit"`)
- "Which links would have to be cut to separate Atlanta from Frankfurt?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| source | string | (required) | Node id where the flow starts |
| sink | string | (required) | Node id where the flow ends (different from source) |
| capacity | string | `weight` | `weight` = edge weight (km on airports); `unit` = 1 per edge, so the flow counts edge-disjoint paths and the cut is the fewest edges to remove; or the name of a numeric edge attribute, such as `airlines` on airports |
| top_k | integer | 10 | How many cut edges to list (1 to 100) |

## Output
```json
{"source": {"id": "MAA", "label": "Chennai International Airport"},
 "sink": {"id": "LIS", "label": "Humberto Delgado Airport (Lisbon Portela Airport)"},
 "capacity": "airlines", "max_flow_value": 73,
 "cut_size": 28, "cut_capacity": 73, "source_side_size": 1, "sink_side_size": 499,
 "cut_edges": [{"from": {"id": "MAA", "label": "Chennai International Airport"},
                "to": {"id": "BOM", "label": "Chhatrapati Shivaji International Airport"}, "capacity": 7}, ...]}
```
`cut_edges` go from the source side to the sink side, largest capacity first; ties are ordered by node ids. The list holds at most `top_k` edges and is shortened further if needed to keep the response under 8 KB. `cut_size` always gives the full number of cut edges. Numbers are rounded to 6 decimals. If the sink cannot be reached, the flow is 0, the cut is empty, and the summary says so. `result_graph_id` is always `null`.

## Graphs it supports
Directed and undirected graphs, weighted or unweighted, including subgraphs registered by other tools. On an unweighted graph `weight` and `unit` are the same (every edge has weight 1). Self-loops are ignored.

## Errors
| Error | Why |
| --- | --- |
| `No graph with id '…'` | Unknown `graph_id`; use `list_graphs` |
| `Give both 'source' and 'sink' as node ids` | A node parameter is missing |
| `Node '…' (parameter 'source'/'sink') is not in graph …. Use lookup_node…` | Not a node id (for example a city name) |
| `source and sink are the same node` | Flow between a node and itself is undefined |
| `Edge … has no numeric attribute '…'. Use capacity = one of: …` | Unknown capacity attribute; the message lists the valid ones |
| `… negative capacity …` | Flows need capacities ≥ 0; use `unit` |
| `top_k must be a whole number from 1 to 100` | Bad `top_k` |
| `Unknown parameter(s): …` | A parameter this tool does not take |
