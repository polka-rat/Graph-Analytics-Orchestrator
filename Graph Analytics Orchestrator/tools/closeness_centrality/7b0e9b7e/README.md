# closeness_centrality

**Author:** 7b0e9b7e · **Tier:** medium · **Category:** centrality

## What it computes
A breadth-first search from every node finds its distance (in hops) to every node it can reach. A node's closeness is `(r - 1) / (sum of distances)`, multiplied by `(r - 1) / (n - 1)`, where `r` is the number of nodes reached (itself included) and `n` the number of nodes. The second factor (Wasserman and Faust) stops a node in a small, separate part of a disconnected graph from looking central. On directed graphs the distance is measured to the node, along incoming edges, as in NetworkX. Time complexity: O(n · (n + m)), about 0.3 s on `airports`.

## When to use it
Questions about who is closest to everyone, or who can spread something fastest, for example:
- "Which airport can be reached from everywhere in the fewest flights?"
- "Who in the karate club is closest to all the other members?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| top_k | integer | 10 | How many results to return (1 to 100) |

## Output
A list of the top_k nodes, highest closeness first (ties broken by node id), each with `closeness` (0 to 1) and `average_distance` (mean hops to or from the nodes it is connected with; null for a node connected to nothing). Scores are rounded to 6 decimals. If `top_k` nodes with long labels would exceed the 8 KB output limit (e.g. `top_k=100` on airports), fewer nodes are listed and the summary says so. `result_graph_id` is always null.

```json
[{"id": "m1", "label": "Member 1 (instructor)", "closeness": 0.568966, "average_distance": 1.757576}]
```

## Graphs it supports
Undirected and directed graphs, connected or not. Edge weights are ignored (distance = number of edges).

## Errors
- Unknown `graph_id`: use list_graphs to see the graphs.
- `top_k` not a whole number from 1 to 100.
- An unknown parameter name.
- A graph with no nodes.
