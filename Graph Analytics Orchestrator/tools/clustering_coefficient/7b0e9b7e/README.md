# clustering_coefficient

**Author:** 7b0e9b7e · **Tier:** easy · **Category:** structure

## What it computes
For each node, the fraction of pairs of its neighbours that are linked to each other: with `d` neighbours there are `d(d-1)/2` possible pairs, and the clustering coefficient is (linked pairs) / (possible pairs). Nodes with fewer than two neighbours get 0. Directed graphs use the directed-triangle definition of Fagiolo (2007), the same as NetworkX. The graph average is the mean over all nodes, including those with 0. Time complexity: O(sum over nodes of degree²), well under a second on `airports`.

## When to use it
Questions about how tightly knit a neighbourhood or a whole network is, for example:
- "How tightly knit is the instructor's circle in the karate club?"
- "How clustered is the airline network on average?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| node | string | (none) | One node to report on; leave out to rank all nodes |
| top_k | integer | 10 | How many of the most clustered nodes to return (1 to 100) |

## Output
With `node`: `{"node": {"id", "label", "clustering", "degree"}, "average_clustering"}`.

```json
{"node": {"id": "m1", "label": "Member 1 (instructor)", "clustering": 0.15, "degree": 16}, "average_clustering": 0.570638}
```

Without `node`: `{"average_clustering", "top_nodes": [{"id", "label", "clustering", "degree"}, ...]}`, sorted by clustering (highest first), ties broken by node id. Scores are rounded to 6 decimals. If `top_k` nodes with long labels would exceed the 8 KB output limit (e.g. `top_k=100` on airports), fewer nodes are listed and the summary says so. `result_graph_id` is always null.

## Graphs it supports
Undirected and directed graphs. Edge weights are ignored (the unweighted coefficient). For directed graphs, `degree` is in-degree + out-degree.

## Errors
- Unknown `graph_id`: use list_graphs to see the graphs.
- Unknown `node`: use lookup_node to find node ids.
- `top_k` not a whole number from 1 to 100.
- An unknown parameter name.
- A graph with no nodes.
