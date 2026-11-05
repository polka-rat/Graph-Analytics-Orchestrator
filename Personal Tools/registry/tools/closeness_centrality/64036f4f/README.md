# closeness_centrality

**Author:** Hayagriv (64036f4f) · **Tier:** medium · **Category:** centrality

## What it computes

The tool runs breadth-first search from every node and computes the reciprocal average hop distance, with the Wasserman-Faust reachable-fraction correction for disconnected graphs. Directed graphs use paths arriving at each node, matching the standard NetworkX convention. Complexity is O(V(V + E)).

## When to use it

Use it for questions such as “Who can reach everyone fastest?” or “Which airports are topologically closest to the rest of the route network?”

## Parameters

| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | required | Id of the graph |
| top_k | integer | 10 | Number of results, from 1 to 100 |

## Output

`result` is a descending list of node references with six-decimal `score` values. Ties are resolved by ascending node id. No result graph is created.

## Graphs it supports

Directed and undirected graphs are supported. Edge weights are intentionally ignored: distances are measured in hops.

## Errors

Unknown graph ids, unsupported parameters, and `top_k` values outside 1–100 return helpful contract errors.
