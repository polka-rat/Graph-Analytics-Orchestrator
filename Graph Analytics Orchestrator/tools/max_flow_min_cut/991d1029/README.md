# max_flow_min_cut

**Author:** 991d1029 · **Tier:** hard · **Category:** paths

## What it computes
Maximum flow from a source to a sink with Edmonds-Karp (repeated BFS shortest augmenting paths, O(V·E²)), then the minimum cut: the edges leaving the set of nodes still reachable from the source in the final residual graph. By the max-flow min-cut theorem the cut's total capacity equals the flow. When several minimum cuts exist, this returns the one closest to the source.

## When to use it
- "Where is the bottleneck between Chennai and London Heathrow?"
- "How many edge-disjoint routes connect member 1 and member 34?" (`capacity="unit"`)

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| source | string | (required) | Node id where flow starts |
| sink | string | (required) | Node id where flow ends (must differ from source) |
| capacity | string | weight | `weight` (edge weight; 1 if unweighted), `unit` (all 1) or a numeric edge attribute such as `airlines` |
| top_k | integer | 10 | Max cut edges to list (1 to 100) |

## Output
`result` is a dict: `max_flow`, `source`, `sink`, `capacity`, `cut_size`, `source_side_size`, `sink_side_size` and `cut_edges` (`{"from": node, "to": node, "capacity"}`, largest capacity first, ties by node ids, at most `top_k`; trimmed if needed to stay under 8 KB). Floats are rounded to 6 decimals. `result_graph_id` is null. If the sink is unreachable the flow is 0 and `cut_edges` is empty.

## Graphs it supports
Directed (arcs follow edge direction) and undirected (each edge carries its capacity both ways); weighted or not. On `airports`, `capacity=weight` means flow in kilometres, which is rarely meaningful: prefer `unit` or `airlines`.

## Errors
Unknown graph, unknown parameter, invalid `top_k`, unknown source or sink, source equal to sink, unknown or non-numeric `capacity` attribute, negative capacity.
