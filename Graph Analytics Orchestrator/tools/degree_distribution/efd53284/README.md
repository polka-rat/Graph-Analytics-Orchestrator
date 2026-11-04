# degree_distribution

**Author:** efd53284 · **Tier:** easy · **Category:** structure

## What it computes
Counts how many nodes have each degree (the number of edges touching a node).
On a directed graph, degree is `in_degree + out_degree`, matching NetworkX's
`G.degree()`. Complexity: O(V + E).

## When to use it
Questions about connectivity spread, for example:
- "How many club members have exactly two friends?"
- "Do most airports have few routes while a handful are hubs?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |

## Output
`result` is a list of `{"degree": d, "count": c}` buckets sorted by degree,
for example `[{"degree": 0, "count": 2}, {"degree": 1, "count": 3}]`.
Degree 0 is included when the graph has isolated nodes. This is a histogram,
not a top-k ranking, so the full distribution is returned; on airports it is
about 5 KB, within the 8 KB response limit. `result_graph_id` is always `null`.

## Graphs it supports
Directed, undirected, weighted and unweighted. Weights are ignored because
degree counts edges, not their weights. An undirected self-loop counts twice.
Disconnected graphs are supported: the histogram counts every component.

## Errors
- Unknown `graph_id`.
- A graph with no nodes.
- Unknown parameters (the tool accepts only `graph_id`).
