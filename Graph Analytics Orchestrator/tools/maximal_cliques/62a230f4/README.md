# maximal_cliques

**Author:** 62a230f4 · **Tier:** hard · **Category:** community

## What it computes
All maximal cliques of an undirected graph using Bron–Kerbosch with pivoting (Tomita-style: pivot maximises |P ∩ N(u)|, ties broken by node id). The reported list is the largest cliques first. Worst-case exponential in n; typical sparse social graphs finish well inside 30 seconds.

## When to use it
Questions about groups where every pair is linked.
- What is the largest group of friends who all know each other?
- How many maximal fully-connected groups are there?

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of an undirected graph |
| top_k | integer | 10 | How many largest cliques to return (1 to 100) |

## Output
`result.max_size` is the size of a largest clique, `n_maximal` is the number of maximal cliques, and `cliques` lists up to top_k of them. Each clique has `size`, `nodes` (id and label, sorted by id), and `graph_id` of a registered subgraph. `result_graph_id` is the first (largest, then lexicographically smallest) clique.

## Graphs it supports
Undirected only (weighted or unweighted; weights are ignored). Directed graphs return an error.

## Errors
- Unknown `graph_id`: use `list_graphs`.
- Directed graph: use karate, lesmis or projects.
- `top_k` outside 1..100.
- Extra parameters.
