# maximal_cliques

**Author:** 92711a92 · **Tier:** hard · **Category:** community

## What it computes
A clique is a set of nodes that are all linked to each other. A clique is *maximal* if no other node can be added to it. The tool lists every maximal clique using **Bron–Kerbosch with Tomita pivoting**:

- R is the clique being built, P the candidates that could extend it, and X the nodes already used (so no clique is reported twice).
- When P and X are both empty, R is maximal.
- At each step it picks a pivot u from P ∪ X with the most neighbours in P, and only branches on the nodes of P that are *not* neighbours of u. Any clique through a neighbour of u is found through u or one of its non-neighbours anyway.

The recursion is written with an explicit stack, so deep searches can't hit Python's recursion limit. Worst case O(3^(n/3)), which is optimal since a graph can have that many maximal cliques. On the provided data it's fast: airports has 17,575 maximal cliques and takes about 0.3 s.

Cliques are sorted largest first, with ties broken by their sorted member ids.

## When to use it
- "What is the largest group in the karate club where everyone is friends with everyone?"
- "Which cliques is Valjean part of?" (`node=...`)

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| node | string | none | Only cliques containing this node |
| min_size | integer | 2 | Smallest clique to return (2 skips isolated nodes) |
| top_k | integer | 10 | How many cliques to return (1 to 100) |

## Output
```json
[{"rank": 1, "size": 5, "graph_id": "karate~1",
  "members": [{"id": "m1", "label": "Member 1 (instructor)"}, {"id": "m14", "label": "Member 14"},
              {"id": "m2", "label": "Member 2"}, {"id": "m3", "label": "Member 3"}, {"id": "m4", "label": "Member 4"}]}, ...]
```
- Each returned clique is registered as a subgraph, and its id is in `graph_id`.
- **`result_graph_id` is the largest clique**, so the next tool can work on it.
- `summary` gives the total number of maximal cliques, the clique number (largest size) and how many cliques have that size.
- If the output would go over 8 KB, the list is shortened and the summary says so.

## Graphs it supports
Undirected graphs. On a directed graph two nodes count as linked if an edge goes either way, the same as NetworkX's `to_undirected()`, and the summary says so. Weights are ignored.

## Errors
- Unknown `graph_id` or `node`, or an unknown extra parameter.
- `top_k` not 1 to 100, or `min_size` not a whole number of at least 1.
- No clique as big as `min_size`: the error gives the largest size, so you can lower it.
- A graph with no nodes.
