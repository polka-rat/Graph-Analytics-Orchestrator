# diameter_eccentricity

**Author:** d69742a9 · **Tier:** medium · **Category:** paths

## What it computes
For every source, it finds shortest-path distances and defines eccentricity as the greatest distance from that source. The diameter is the greatest eccentricity; the center minimizes eccentricity and the periphery maximizes it. It uses BFS on unweighted graphs and Dijkstra's algorithm on weighted graphs, so it runs in `O(V(V+E))` unweighted or `O(V E log V)` weighted time.

## When to use it
Use it for “How far apart are the most distant nodes?”, “Which nodes are at the center?”, or “Which nodes are peripheral?”

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | required | Id of the graph |
| top_k | integer | 10 | Maximum returned entries, from 1 to 100 |

## Output
`result` contains the diameter, ranked eccentricity node references, and bounded center and periphery node references. It does not create a subgraph.

## Graphs it supports
Connected directed and undirected graphs, weighted or unweighted. Directed distances follow outgoing edges. Disconnected graphs and negative weights return errors.

## Errors
It returns an error for an unknown graph, invalid `top_k`, a disconnected or empty graph, or negative edge weights.

