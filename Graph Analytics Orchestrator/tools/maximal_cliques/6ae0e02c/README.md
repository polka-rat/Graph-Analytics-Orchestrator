# maximal_cliques

**Author:** 6ae0e02c · **Tier:** hard · **Category:** community

## What it computes
Every maximal clique of an undirected graph. A clique is a set of nodes in which each node is directly connected to every other node; it is *maximal* when no further node can be added while keeping that property. The search is Bron–Kerbosch with pivoting: it grows a clique `R` from a candidate set `P`, moves handled nodes into `X`, and reports `R` when both are empty. The pivot is the node in `P ∪ X` with the most neighbours in `P`, which skips branches that cannot yield a new maximal clique. All maximal cliques are enumerated — nothing is pruned — so `total_cliques` is exact. Worst case is exponential in the number of nodes, as for any maximal-clique enumeration, but pivoting keeps the provided graphs fast.

## When to use it
- "What is the largest group of members who all know each other?" (`karate`)
- "How many tightly knit groups does this network contain?" (`lesmis`)

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the undirected graph |
| top_k | integer | 10 | How many of the largest cliques to return (1 to 100) |

## Output
`result` = `{"total_cliques": int, "cliques": [{"clique", "size", "graph_id", "nodes"}]}`. `total_cliques` counts **every** maximal clique found, not just those returned. Cliques are sorted by size descending, ties by their sorted node ids. Each returned clique lists **all** of its members — a clique is never truncated, because hiding members would misrepresent it. Each clique is registered as a subgraph and its id appears as `graph_id`; `result_graph_id` is the largest clique's id.

If the requested cliques do not fit in the 8 KB output limit, the smallest are dropped and the summary says how many are shown.

## Graphs it supports
Undirected graphs only. A clique is an undirected idea — "everyone connected to everyone" has no natural meaning when edges have a direction — so directed graphs are rejected with an explanation. Weights are ignored. Self-loops are removed.

## Errors
- Unknown `graph_id`, or a `graph_id` that is not a string.
- The graph is directed, e.g. `airports`: the message names the graph and suggests `karate` or `lesmis`.
- `top_k` is not a whole number from 1 to 100 (booleans are rejected).
- Any unknown parameter name.
- A graph with no nodes.
