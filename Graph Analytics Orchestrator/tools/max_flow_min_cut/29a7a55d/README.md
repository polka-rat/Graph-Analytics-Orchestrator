# max_flow_min_cut

**Author:** 29a7a55d · **Tier:** hard · **Category:** paths

## What it computes
Maximum flow from `source` to `sink` with the **Edmonds–Karp** algorithm, plus the
**minimum cut** it implies. Edge weights are capacities; an undirected edge acts as
two directed edges with the same capacity. The algorithm keeps a residual-capacity
network `res[u][v]`, repeatedly finds a *shortest* source→sink path with BFS and
pushes the path's bottleneck through it (decreasing forward, increasing reverse
residuals) until no augmenting path remains. Each BFS costs O(E) and the number of
augmentations is O(V·E) in the worst case, giving O(V·E²) overall — but on the
provided datasets it finishes in well under a second.

The minimum cut is read off the final residual network: the set `S` of nodes still
reachable from the source, and the original edges leading from `S` to the rest. By
the max-flow min-cut theorem their total capacity equals the maximum flow, which is
what the tool reports.

## When to use it
Questions about throughput and bottlenecks between two nodes:
- "Where is the bottleneck between source and sink?"
- "What is the maximum flow from airport A to airport B?"
- "Which edges, if removed, would separate A from B?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| source | string | (required) | Id of the source node |
| sink | string | (required) | Id of the sink node, ≠ source |
| top_k | integer | 10 | How many cut edges to list (1 to 100) |

## Output
`result` contains `source` and `sink` (id + label), `flow_value` (rounded to 6
decimals) and `min_cut`: `cut_edges_count`, `cut_edges` (up to `top_k` entries
`{"source", "target", "capacity"}`, sorted; the count is always exact),
`source_side_count` and `source_side` (up to 10 node refs, count exact).
No `result_graph_id`.

## Graphs it supports
Directed and undirected graphs, weighted or not (unweighted ⇒ every capacity is 1.0).
Antiparallel directed edges (A→B and B→A) are supported: they share the residual
network, which affects neither the flow value nor the canonical cut. If the sink is
unreachable, the flow is 0 and the cut is empty.

## Errors
- Unknown `graph_id` → use `list_graphs`.
- `source` or `sink` not in the graph → use `lookup_node` to find ids.
- `source == sink` → a flow needs two different endpoints.
- `top_k` not an integer from 1 to 100.
