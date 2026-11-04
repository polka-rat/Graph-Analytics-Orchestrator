# maximal_cliques

**Author:** 6e31812a · **Tier:** hard · **Category:** community

## What it computes
A clique is a set of nodes in which every pair is connected; it is maximal if no other node can be added. The tool lists all maximal cliques with the **Bron–Kerbosch algorithm with pivoting** (Tomita et al., 2006), then returns the largest ones.

The recursion keeps three sets: R (the clique being built), P (nodes that could still extend R) and X (nodes already tried, to avoid reporting the same clique twice). When P and X are both empty, R is maximal. At each step it chooses a pivot u in P ∪ X with the most neighbours in P and branches only on candidates that are not neighbours of u, because any maximal clique must contain u or a non-neighbour of u. Worst case O(3^(n/3)), which is optimal because a graph can have that many maximal cliques. On airports (500 nodes, 17,575 maximal cliques) it takes about 0.6 s.

## When to use it
- "What is the largest group where everyone knows everyone?" / "What is the clique number of the karate club?"
- "Which tightly knit groups is Valjean part of?" (pass `node`)
- "Which airports are all connected to each other by direct routes?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| top_k | integer | 10 | How many of the largest cliques to return (1 to 100) |
| node | string | none | Only count and return the cliques that contain this node id |
| mutual_only | boolean | false | Directed graphs: count a pair as connected only if edges go both ways |

## Output
```json
{"graph_id": "karate", "node": null, "clique_number": 5, "maximal_cliques": 36,
 "largest_cliques": 2, "requested": 10, "returned": 10,
 "cliques": [{"rank": 1, "size": 5, "graph_id": "karate~1", "members_truncated": false,
              "members": [{"id": "m1", "label": "Member 1 (instructor)"}, "..."]}, "..."]}
```

Cliques are sorted by size (largest first), with ties broken by their sorted member ids; members are sorted by id. Each returned clique is registered as a subgraph (`graph_id`), and `result_graph_id` is the largest one. If listing `top_k` cliques would exceed the 8 KB output limit, fewer are returned (`returned` < `requested`) and the summary says so. On airports, where the largest clique has 24 airports, about four cliques fit.

## Graphs it supports
Undirected graphs. A directed graph is treated as undirected: an edge in either direction connects two nodes, as in `G.to_undirected()` in NetworkX; with `mutual_only=true` both directions are required (`to_undirected(reciprocal=True)`). Weights and self-loops are ignored. In a graph with no edges every node is its own clique of size 1.

## Errors
- Unknown `graph_id` → use `list_graphs`.
- `node` not in the graph → use `lookup_node` to find the id.
- `top_k` not a whole number from 1 to 100; `mutual_only` not true/false.
- Unknown parameter → the error lists the accepted ones.
- A graph with no nodes.
