# diameter_eccentricity

**Author:** 991d1029 · **Tier:** medium · **Category:** paths

## What it computes
Runs a BFS from every node to get its eccentricity (hop distance to the farthest node). Diameter = max eccentricity, radius = min, center = nodes with eccentricity equal to the radius, periphery = nodes with eccentricity equal to the diameter. Time O(V·(V+E)). Edge weights are ignored (hop counts).

## When to use it
- "How far apart are the most distant nodes in the karate club network?"
- "Which airports form the center of the route network?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| top_k | integer | 10 | Max center and periphery nodes to list (1 to 100) |
| node | string | none | Optional node whose eccentricity is also returned |

## Output
`result` is a dict: `diameter`, `radius`, `center_size`, `periphery_size`, `center` and `periphery` (node refs sorted by id, at most `top_k`; all center nodes have eccentricity = radius, all periphery nodes = diameter; lists are trimmed if needed to stay under 8 KB), `farthest_pair` (the smallest-id periphery node and its smallest-id farthest node), and `node` if requested. `result_graph_id` is null.

## Graphs it supports
Undirected graphs that are connected, and directed graphs that are strongly connected (paths follow edge direction). Weighted or not. Of the provided graphs: karate, lesmis and airports work; courses and projects return an error.

## Errors
Unknown graph, unknown parameter, invalid `top_k`, unknown `node`, empty graph, disconnected / not strongly connected graph (the message names the right components tool).
