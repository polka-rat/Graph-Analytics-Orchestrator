# personalized_pagerank

**Author:** c52598eb · **Tier:** medium · **Category:** centrality

## What it computes
Personalized PageRank from one seed node. A random walker at each step follows an out-edge with probability `alpha` (choosing edges in proportion to their weight) or jumps back to the seed with probability `1 - alpha`. A walker at a node with no out-edges also jumps back to the seed. The score of a node is the long-run fraction of time the walker spends there, so nodes close to the seed and reachable by many paths score highest.

The stationary vector is computed by power iteration until the L1 change is below 1e-12, with at most 1000 iterations. It matches `networkx.pagerank(G, alpha=alpha, personalization={seed: 1})`, including the dead-end rule, which networkx applies by default when a personalization vector is given. Time: O(n + m) per iteration, typically under 200 iterations; well under a second on airports.

## When to use it
Questions about relevance to one particular node, rather than global importance:
- "Which airports are most closely tied to Delhi?" → `{"graph_id": "airports", "node": "DEL", "top_k": 5}`
- "Who is in the instructor's inner circle?" → `{"graph_id": "karate", "node": "m1"}`

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| node | string | (required) | Seed node id (use lookup_node to find it from a name) |
| top_k | integer | 10 | How many results to return (1 to 100) |
| alpha | number | 0.85 | Probability of following an edge rather than jumping back to the seed; strictly between 0 and 1 |

## Output
`result` is a list of nodes, highest score first, ties broken by node id (ascending). Each entry has `id`, `label` and `score` (rounded to 6 decimals). Scores sum to 1 over all nodes, and the seed is usually first. The summary names the most relevant node other than the seed. No `result_graph_id`.

```json
{"id": "JFK", "label": "John F Kennedy International Airport", "score": 0.016154}
```

The response always stays under 8 KB. With `top_k=100` on airports the long labels would exceed it, so trailing entries are dropped and the summary says how many are shown.

## Graphs it supports
Directed and undirected, weighted and unweighted. On weighted graphs the walk follows edges in proportion to weight, as networkx does by default. For airports the weight is distance in km, so longer routes get more of the walk. Nodes the seed cannot reach score 0.

## Errors
- Unknown `graph_id` → use list_graphs.
- Missing or unknown `node` → use lookup_node.
- `top_k` not a whole number from 1 to 100.
- `alpha` not a number strictly between 0 and 1.
- Unknown parameter names.
