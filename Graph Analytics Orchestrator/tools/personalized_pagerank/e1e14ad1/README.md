# personalized_pagerank

**Author:** e1e14ad1 · **Tier:** medium · **Category:** centrality

## What it computes
Personalized PageRank (random walk with restart) from one source node. A surfer follows a random out-edge with probability `damping`, otherwise jumps back to the source. The long-run share of time spent at each node is its score:

```
pi = damping * P^T pi + (1 - damping) * e_source
```

Solved by power iteration (stops when the L1 change is below 1e-10, at most 5000 iterations; damping 0.99 can need ~2400 on slow-mixing graphs such as bipartite ones). Each iteration is O(edges), and the error shrinks by at least a factor `damping` per iteration. Scores are visit probabilities and sum to 1 over all nodes, source included; the returned ranking is only the top `top_k` without the source, so it sums to less than 1.

Conventions that change the numbers:
- **Dangling nodes** (no out-edges) send their probability back to the source, which keeps scores local to it.
- **Weights are ignored by default.** With `use_weights=true`, an edge is followed in proportion to its weight, so weights must mean tie strength (shared chapters in `lesmis`). In `airports` the weight is distance in km, so leave it off.
- **Undirected edges** can be walked in both directions.
- **The source always scores at least `1 - damping`**, so it is left out of the ranking by default and reported as `source_score`.

## When to use it
- "What is most relevant to this paper / person / airport?"
- "Which nodes are closest to Alice overall, counting every route and not only the shortest?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| node | string | (required) | Node id of the source (use `lookup_node` for names) |
| damping | number | 0.85 | Probability of following an edge, in [0, 1) |
| use_weights | boolean | false | Use edge weights as tie strength |
| include_source | boolean | false | Also list the source in the ranking |
| top_k | integer | 10 | How many nodes to return (1 to 100) |

## Output
`result`: `source`, `damping`, `weighted`, `source_score`, `scored_nodes` (nodes with a positive score, source excluded unless `include_source`), `iterations`, `converged`, and `ranking`, a list of `{id, label, score}` sorted by score (ties by id). The list is shortened if long labels would exceed 8 KB. `result_graph_id` is `null`.

## Graphs it supports
Directed and undirected, weighted or not. Nodes that cannot be reached from the source get no score and are not listed.

## Errors
- Unknown graph, or unknown / non-string node (use `lookup_node`).
- `damping` not a number in [0, 1).
- `use_weights` or `include_source` not a boolean.
- `top_k` not a whole number from 1 to 100.
- Unknown parameter names.

A source with nothing reachable (for example a sink in a DAG, or `damping=0`) is **not** an error: the ranking is empty and the summary says so.
