# personalized_pagerank

**Author:** e7c02e9e · **Tier:** medium · **Category:** centrality

## What it computes
PageRank where the random surfer, instead of teleporting to a uniformly random node, teleports back to one or more
**seed** nodes. A node's score is the long-run fraction of time the surfer spends there, so high scores mean "close to
and well connected from the seed". Solved by power iteration (NumPy, tolerance 1e-12):

`x <- d * (P^T x + dangling_mass * p) + (1 - d) * p`

where `p` is uniform over the seeds, `d` is the damping factor, and the mass of dead-end nodes (no outgoing edges,
possible in directed graphs) is sent back to the seeds, the same convention as NetworkX. Each iteration is O(V+E).

## When to use it
- "What is most relevant to Valjean?" (`graph_id=lesmis`, node = Valjean's id)
- "Which airports are most closely tied to Chennai?"
- Recommendation-style questions: "who should Member 1 look at next?" (use `exclude_seeds=true`)

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| node | string | (required) | Seed node id |
| seeds | array of strings | none | Extra seed node ids; teleport probability is split equally among all seeds |
| damping | number | 0.85 | Probability of following an edge, `0 <= damping < 1` |
| top_k | integer | 10 | How many nodes to return (1 to 100) |
| use_weights | boolean | true | Follow heavier edges more often, on weighted graphs. Set false for distance weights (airports) |
| exclude_seeds | boolean | false | Leave seed nodes out of the ranking |

## Output
`result` is a list of `{"id", "label", "score", "rank"}`, best first, ties broken by node id, scores rounded to 6 decimals.
Scores over all nodes sum to 1 (the list shows only the top `top_k`). `result_graph_id` is null.

## Graphs it supports
Directed and undirected; weighted and unweighted. Undirected graphs treat every edge as two-way. Weights are used
only if the graph is weighted *and* `use_weights` is true; NetworkX uses weights by default, so the default matches it.
Subgraphs registered by other tools work too.

## Errors
- unknown graph; unknown seed node (message points to `lookup_node`); no seed given
- `damping` outside [0, 1); `top_k` outside 1 to 100; non-boolean flags; unrecognised parameter
- negative edge weight with `use_weights=true`
- `exclude_seeds=true` when every node is a seed
