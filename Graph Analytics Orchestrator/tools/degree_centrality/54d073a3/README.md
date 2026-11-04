# degree_centrality

**Author:** 54d073a3 · **Tier:** easy · **Category:** centrality

## What it computes
Degree centrality: the number of direct connections of each node divided by $n-1$, where $n$ is the number of nodes (the same normalisation as NetworkX's `degree_centrality`). On directed graphs the degree is in-degree + out-degree, and the ranking can instead use in-degree or out-degree alone. Edge weights are ignored. One pass over all nodes and edges, so $O(n + m)$ time plus $O(n \log n)$ for sorting.

## When to use it
Questions about which nodes are the most connected.
- "Which airport has the most direct routes?"
- "Who has the most friends in the karate club?"
- "Which airport has the most incoming routes?" (use `direction="in"`)

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| top_k | integer | 10 | How many results to return (1 to 100) |
| direction | string | "total" | Directed graphs only: "total" (in + out), "in" or "out". Ignored on undirected graphs. |

## Output
`result` is a list of up to `top_k` nodes, highest first. Ties are broken by node id (ascending). Each entry has `id`, `label`, `score` (rounded to 6 decimals) and the raw `degree`; on directed graphs it also has `in_degree` and `out_degree`.

```json
{"id": "FRA", "label": "Frankfurt am Main Airport", "score": 0.847695,
 "degree": 423, "in_degree": 212, "out_degree": 211}
```

It does not return `result_graph_id` (it is not a subgraph tool). If the list would exceed the 8 KB response limit, it is shortened and the summary says so.

## Graphs it supports
Directed and undirected, weighted and unweighted. Weights are ignored. A self-loop counts twice in an undirected degree, as in NetworkX. A graph with a single node gets score 1.0.

## Errors
- Unknown `graph_id`: the error says to use `list_graphs`.
- `top_k` not a whole number from 1 to 100.
- `direction` not one of total, in, out.
- Any unknown parameter.
- A graph with no nodes.
