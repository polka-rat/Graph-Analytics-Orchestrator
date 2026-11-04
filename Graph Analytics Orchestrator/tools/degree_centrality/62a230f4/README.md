# degree_centrality

**Author:** 62a230f4 · **Tier:** easy · **Category:** centrality

## What it computes
Degree centrality of each node: its degree divided by n-1 (the NetworkX normalisation). On a directed graph the total score uses in-degree plus out-degree, and the tool also reports separate in and out scores. Ranking is O(n + m).

## When to use it
Questions about the most connected nodes, hubs, or airports with the most direct routes.
- Which karate member has the most friends?
- Which airport has the most incoming non-stop routes?

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| top_k | integer | 10 | How many results to return (1 to 100) |
| mode | string | total | Rank by `total`, `in`, or `out` degree centrality |

## Output
`result` is a list of node objects with `id`, `label` and `score`. Directed graphs also include `in_score` and `out_score`. Ties break by node id, ascending. `result_graph_id` is null.

## Graphs it supports
Directed and undirected, weighted and unweighted. Edge weights are ignored; only the number of incident edges counts.

## Errors
- Unknown `graph_id`: use `list_graphs`.
- `top_k` outside 1..100.
- Unknown `mode` or extra parameters.
