# betweenness_centrality

**Author:** d69742a9 · **Tier:** hard · **Category:** centrality

## What it computes
Brandes' algorithm counts how often each node lies on shortest paths between other nodes. Results use NetworkX-compatible normalized centrality and are sorted by descending score then node id. The unweighted complexity is `O(VE)`; weighted graphs use Dijkstra and take `O(VE log V)`.

## When to use it
Use it for “Who are the key brokers between groups?” or “Which nodes control many routes between other nodes?”

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | required | Id of the graph |
| top_k | integer | 10 | Number of results, from 1 to 100 |

## Output
`result` is a top-k list of node references with normalized scores. It does not create a subgraph.

## Graphs it supports
Directed and undirected, weighted and unweighted graphs. Weighted edges must be non-negative; unreachable pairs contribute zero.

## Errors
It returns an error for an unknown graph, invalid `top_k`, or negative edge weights.

