# max_flow_min_cut

**Author:** edba08e8 · **Tier:** hard · **Category:** paths

## What it computes
Maximum flow from `source` to `sink` with **Edmonds-Karp** (Ford-Fulkerson where each augmenting path is found by BFS,
so it is a shortest path in edges). Time O(V·E²) worst case; far faster in practice. The residual network is stored in
parallel arrays (edge `i` and its reverse `i^1`), nodes are indexed in sorted id order, so results are deterministic.
The **minimum cut** is read from the final residual network: S = nodes reachable from the source through edges with
remaining capacity; the cut edges are the original edges leaving S. Its capacity equals the max flow (max-flow min-cut theorem).

## When to use it
- "Where is the bottleneck between Chennai and Delhi?"
- "How many edge-disjoint routes connect member 1 and member 34?" (unweighted graph, capacity 1 each)

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| source | string | (required) | Node id where the flow starts |
| sink | string | (required) | Node id where the flow ends (must differ from source) |
| top_k | integer | 10 | How many cut edges to list (1 to 100), largest capacity first |

## Output
```
{"max_flow": 12.0, "source": {id,label}, "sink": {id,label}, "cut_capacity": 12.0,
 "cut_edges_total": 5, "cut_edges_returned": 5, "source_side_size": 20, "sink_side_size": 14,
 "cut_edges": [{"from": {id,label}, "to": {id,label}, "capacity": 4.0}, ...]}
```
`result_graph_id` is `null`. The list is shortened if needed to keep the response under 8 KB.
If the sink cannot be reached from the source, the tool returns `status: "error"` explaining that no flow is possible.

## Graphs it supports
- Directed: an edge `u -> v` of weight `w` carries up to `w` from u to v.
- Undirected: an edge carries up to `w` in either direction (cut edges are listed oriented from source side to sink side).
- Weighted: weights are capacities. Unweighted: every capacity is 1. Self-loops and edges with weight <= 0 are ignored.
- Floating-point capacities are handled with a 1e-9 tolerance; results are rounded to 6 decimals.

## Errors
- Unknown graph id, unknown `source` or `sink` node (suggests `lookup_node`), missing `source`/`sink`.
- `source` equals `sink`.
- No path from `source` to `sink` (different components, or wrong direction in a directed graph).
- Invalid `top_k`, unknown extra parameters.
