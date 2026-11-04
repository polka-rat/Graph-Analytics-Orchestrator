# Maximal cliques

Author: ab9fb3a3 · Tier: hard · Category: community

Implements Bron–Kerbosch with pivoting using an explicit stack. R is the current clique, P possible extensions, and X previously explored extensions. A clique is emitted only when both P and X are empty. The pivot maximises its neighbours in P, with node-ID tie breaking. The stack avoids Python recursion-depth failures.

Use for: “Which friendship groups are completely connected?” or “What is the largest clique?” A maximal clique cannot be extended; a maximum clique is the largest maximal clique. This tool enumerates maximal cliques and retains the largest top_k, not just cliques of maximum size.

| Parameter | Default | Meaning |
| --- | --- | --- |
| graph_id | required | Registered nonempty undirected graph |
| top_k | 10 | 1–100 largest maximal cliques to return |

Supports disconnected, weighted and unweighted undirected graphs. Weights and self-loops are ignored; isolated nodes are singleton maximal cliques. Directed and empty graphs return helpful errors. Enumeration has exponential worst-case runtime; use small graphs such as karate and lesmis. Ranking is descending clique size, then lexicographic ascending tuple of member IDs. Members sort by ID.

`result` is a list of objects containing `size`, complete `nodes` (each with id and label), and `graph_id`. Each clique is registered as an induced subgraph; result_graph_id points to the first/largest one so another tool can analyse it. The summary gives the total number of maximal cliques. Generated IDs depend on the store counter; fresh equivalent stores yield identical output.

For edges a–b, b–c, a–c and c–d, results are {a,b,c} and {c,d}. A displayed clique is never truncated. If full membership exceeds 8 KB, the tool returns an error asking for fewer cliques or a smaller graph.

Worst-case enumeration is exponential (up to 3^(V/3) maximal cliques), with additional set-operation costs. Adjacency needs O(V+E) memory, the explicit search stack up to O(V²), and retained top-k membership O(kV). It does not retain all enumerated cliques.

Errors: unknown graph, directed/empty graph, invalid top_k, unknown parameters, or oversized output.

```sh
.venv/bin/python run_tool.py registry/tools/maximal_cliques/ab9fb3a3 graph_id=karate top_k=5
.venv/bin/python -m pytest registry/tools/maximal_cliques/ab9fb3a3/tests
```
