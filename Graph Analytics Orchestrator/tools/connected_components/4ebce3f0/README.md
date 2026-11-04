# connected_components

**Author:** 4ebce3f0 · **Tier:** easy · **Category:** community

## What it computes
Splits a graph into connected components: maximal groups of nodes that can reach each other through edges. It runs a breadth-first search from every node not yet visited, following edges in both directions; each search collects one component. Time O(V + E), memory O(V).

## When to use it
For questions about whether a network holds together, how many separate parts it has, and which part a node belongs to. Examples:
- "Is the karate club network connected?"
- "How many separate groups are there in the projects graph, and which project has nobody working on it?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| top_k | integer | 10 | How many components to return, largest first (1 to 100) |
| node | string | none | Optional node id; the result then says which component it is in |

## Output
`result` is an object:
- `num_components`, `largest_size`, `isolated_nodes` (components of size 1), `connectivity` (`"undirected"` or `"weak"`)
- `components`: up to `top_k` components, largest first, each with `component` (rank), `size`, `graph_id` (the registered subgraph), `members` (up to 10 nodes as `{id, label}`, sorted by id) and `members_shown`
- `node` (only if `node` was given): `{id, label, component, component_size}`

`result_graph_id` is the largest component, or the component containing `node` if given.

Example (`graph_id="projects"`): 2 components; component 1 has 25 nodes (`projects~1`), component 2 is the isolated node P08 (Project 08).

Ties between components of equal size are broken by their smallest node id. If the output would pass 8 KB, fewer members per component are listed, then fewer components; the counts are always complete.

## Graphs it supports
Undirected graphs, weighted or not (weights are ignored). Directed graphs are accepted: edge direction is ignored, so the result is the weakly connected components (`connectivity: "weak"`). For strongly connected components use `strongly_connected_components`.

## Errors
- Unknown `graph_id`: use `list_graphs`.
- Unknown parameter: the tool lists the parameters it takes.
- `top_k` not a whole number from 1 to 100.
- `node` not in the graph: use `lookup_node` to find the id.
- The graph has no nodes.