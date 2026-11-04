# degree_centrality

**Author:** c52598eb · **Tier:** easy · **Category:** centrality

## What it computes
For every node it counts the edges that touch it and divides by `n - 1`, the largest possible degree, so scores lie between 0 and 1 (the same normalisation as `networkx.degree_centrality`). On a directed graph the count is incoming plus outgoing edges by default, or only one direction with `direction="in"` / `"out"` (matching `in_degree_centrality` / `out_degree_centrality`). It then returns the top_k nodes. Time: O(n + m) to count, O(n log n) to sort.

## When to use it
Questions about who or what has the most direct connections:
- "Which airport has the most direct routes?" → `{"graph_id": "airports"}`
- "Which airports have the most departures?" → `{"graph_id": "airports", "direction": "out"}`
- "Who has the most friends in the karate club?" → `{"graph_id": "karate", "top_k": 3}`

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| top_k | integer | 10 | How many results to return (1 to 100) |
| direction | string | `"total"` | Directed graphs only: `"total"` (in + out), `"in"` or `"out"`. Ignored on undirected graphs |

## Output
`result` is a list of nodes, highest score first, ties broken by node id (ascending). Each entry has `id`, `label`, `score` (rounded to 6 decimals) and the raw `degree`; on directed graphs also `in_degree` and `out_degree`. No `result_graph_id`.

```json
{"id": "FRA", "label": "Frankfurt am Main Airport", "score": 0.847695, "degree": 423, "in_degree": 212, "out_degree": 211}
```

The response always stays under 8 KB. If the raw counts would push it over (for example `top_k=100` on airports, whose labels are long), the raw counts are dropped and only `id`, `label` and `score` are kept. If it is still too large, trailing entries are dropped and the summary says so.

## Graphs it supports
Directed and undirected, weighted and unweighted. Weights are ignored because degree counts edges, not distances. Works on subgraphs registered by other tools.

## Errors
- Unknown `graph_id` → use list_graphs.
- `top_k` not a whole number from 1 to 100.
- `direction` not one of `total`, `in`, `out`.
- Unknown parameter names.
- A graph with no nodes.
