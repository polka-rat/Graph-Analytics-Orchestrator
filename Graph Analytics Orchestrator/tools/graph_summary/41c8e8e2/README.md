# graph_summary

**Author:** 41c8e8e2 · **Tier:** easy · **Category:** structure

## What it computes
A one-call overview of a graph: node and edge counts, density, average degree, degree range, the highest-degree node, isolated nodes, self-loops and (weakly) connected components. Directed graphs also get in/out average degree and reciprocity; weighted graphs get total and average weight. One pass over the nodes and edges plus a DFS for components: O(V + E).

## When to use it
- "How big is this network?"
- "How dense is the karate club graph, and is it connected?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |

## Output
`result` is an object (not a node list):
```json
{"graph_id": "karate", "directed": false, "weighted": false, "nodes": 34, "edges": 78,
 "density": 0.139037, "average_degree": 4.588235, "min_degree": 1, "max_degree": 17,
 "highest_degree_node": {"id": "m34", "label": "...", "degree": 17},
 "isolated_nodes": 0, "self_loops": 0, "connected_components": 1, "largest_component_size": 34}
```
- `density` = m / (n(n-1)) for directed graphs, 2m / (n(n-1)) for undirected ones (as in NetworkX).
- `average_degree` = 2m / n for both kinds (for directed graphs this counts in + out). `average_out_degree` and `average_in_degree` (= m / n) are added for directed graphs.
- Degree of a node in a directed graph is in-degree + out-degree. Ties for the highest-degree node go to the smaller node id.
- Components ignore edge direction (weak connectivity).
- `result_graph_id` is always `null`.

## Graphs it supports
Directed and undirected, weighted and unweighted. Subgraphs created by other tools also work.

## Errors
- Unknown `graph_id`: error telling the caller to use `list_graphs`.
- A graph with no nodes: error (nothing to summarise).
- Any unknown parameter: error naming it.
