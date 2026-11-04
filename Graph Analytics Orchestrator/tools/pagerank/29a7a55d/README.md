# pagerank

**Author:** 29a7a55d · **Tier:** medium · **Category:** centrality

## What it computes
PageRank by power iteration. Each node starts with rank 1/n; every iteration a node
gives each outgoing link `damping × rank / out-weight` (weights are proportional to
link strength), the rank of dangling nodes (no outgoing edges) is spread uniformly,
and `(1 − damping)/n` is added everywhere as the teleport probability. The iteration
stops when the L1 change falls below `n × 1e-12` (max 1000 iterations), so the scores
are accurate far beyond the 6 decimals that are returned. One iteration costs O(E)
with NumPy; a full run on the largest dataset (500 nodes, 20k edges) takes a fraction
of a second.

## When to use it
Questions about overall importance that take the whole graph into account:
- "Which papers are most influential?"
- "Which airport is the strongest hub overall?"
- "Who are the top-5 most important characters?"

Unlike degree centrality, PageRank rewards being linked *from important nodes*, not
just having many links.

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| damping | number | 0.85 | Probability of following a link (0 to 1) |
| top_k | integer | 10 | How many top nodes to return (1 to 100) |

## Output
`result` is a list of up to `top_k` entries `{"id", "label", "score"}`, sorted by
score descending; equal scores are ordered by node id ascending. Scores are rounded
to 6 decimals and sum to ~1 across the whole graph. No `result_graph_id`.

## Graphs it supports
Directed and undirected graphs, weighted or unweighted (weights scale link strength;
unweighted graphs treat every link as 1.0). Dangling nodes are handled like in
NetworkX: their rank is redistributed uniformly. Requires positive edge weights and
`damping` between 0 and 1.

## Errors
- Unknown `graph_id` → use `list_graphs`.
- `damping` outside [0, 1] or not a number.
- `top_k` not an integer from 1 to 100.
- Non-convergence (only possible for damping very close to 1) → retry with smaller damping.
