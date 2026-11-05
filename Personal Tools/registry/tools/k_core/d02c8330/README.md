# k_core (d02c8330) ↪

**Answers:** "What is the tightly connected core?", "What is X's core number?", "Which nodes keep at least k links among themselves?"

## Algorithm
Batagelj–Zaversnik peeling with degree buckets, O(n + m): repeatedly remove a node of minimum
current degree. Its core number is the largest minimum degree seen so far. Nodes are bucketed in
sorted id order, so the run is deterministic. The k-core is the set of nodes with core number ≥ k.

## Parameters
| name | type | default | meaning |
|---|---|---|---|
| graph_id | string | required | graph to analyse |
| k | int ≥ 0 | max core number | core order; omit to get the densest core |
| node | string | none | also report this node's core number |
| top_k | int | 10 | number of core members to list (1–100) |

## Output
`k`, `max_core`, `core_size`, `core_edges`, `core_number_counts` (how many nodes have each core
number), `members` (core number desc, then id asc) and optionally `node`. The k-core is registered
with `store.subgraph`, and its id is returned in `result_graph_id` for chaining with other tools.

## Edge cases
If `k` is larger than the maximum core number, the error names the maximum and says to use a smaller k.
Directed graphs are treated as undirected (noted in the summary). Weights are ignored, self-loops skipped.
Unknown graph or node, a non-integer or negative k, bad `top_k` and unknown parameters return errors.

## Example
`python run_tool.py registry/tools/k_core/d02c8330 graph_id=karate` returns the 4-core of karate (10 nodes).
