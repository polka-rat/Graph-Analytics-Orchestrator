# node_similarity

**Author:** 29a7a55d · **Tier:** easy · **Category:** structure

## What it computes
Takes two nodes and compares their neighbour sets. It returns the number of common
neighbours, the size of the union of both neighbourhoods and the Jaccard score
`|A ∩ B| / |A ∪ B|`, where 1.0 means both nodes connect to exactly the same others
and 0.0 means they share nobody. Runs in O(deg(a) + deg(b)) time using hash sets,
plus O(k log k) to sort the common neighbours.

On directed graphs direction is ignored: `Graph.undirected_neighbors` merges incoming
and outgoing edges, so a neighbour is anyone connected in either direction.

## When to use it
Questions about how similar two nodes' connections are, for example:
- "How similar are Alice's and Bob's connections?"
- "Do Airports A and B share destinations?"
- "Who do these two people both know?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| node_a | string | (required) | Id of the first node |
| node_b | string | (required) | Id of the second node, different from `node_a` |

## Output
`result` is an object: `node_a` and `node_b` (each `{"id", "label", "degree"}`),
`common_neighbors_count`, `common_neighbors` (up to 20 node refs with id and label —
the count is always exact even when the list is capped), `union_size` and `jaccard`
(rounded to 6 decimals). No `result_graph_id`.

Example: `{"node_a": {"id": "m1", ...}, "jaccard": 0.117647, "common_neighbors_count": 4, ...}`

## Graphs it supports
Any graph in the store, directed or undirected, weighted or not (weights are ignored:
similarity depends only on adjacency).

## Errors
- Unknown `graph_id` → use `list_graphs`.
- `node_a` or `node_b` not in the graph → use `lookup_node` to find ids.
- `node_a == node_b` → a node is not compared with itself; choose two different nodes.
- Unknown extra parameters → the tool takes only `graph_id`, `node_a`, `node_b`.
