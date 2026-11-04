# ego_network

**Author:** e1e14ad1 · **Tier:** easy · **Category:** subgraph (returns `result_graph_id`)

## What it computes
The ego network of a node: the node (the *ego*), its immediate neighbours and **every edge among them**, neighbour-neighbour edges included. Neighbours come straight from adjacency in O(degree); the induced subgraph is registered with the store (one O(|E|) scan), and its node and edge counts are read back from the registered graph so they always match `result_graph_id`.

## When to use it
- "Show me Bob's immediate network." / "Who is directly connected to Chennai?"

Use `k_hop_neighborhood` for anything beyond one hop.

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| node | string | (required) | Node id of the ego (use `lookup_node` for names) |
| direction | string | `both` | Directed graphs only: `out`, `in` or `both`. Ignored for undirected graphs |
| top_k | integer | 10 | Neighbours to list in the sample (1 to 100) |

## Output
`result`: `ego` (id, label), `neighbors` (the full count), `nodes` and `edges` of the ego network, and `neighbor_sample`, up to `top_k` neighbours sorted by id (shortened if long labels would exceed 8 KB). `result_graph_id` is the registered ego-network subgraph.

Example (karate, `m1`): 16 neighbours, 17 nodes, 34 edges.

## Graphs it supports
Directed and undirected, weighted or not; weights are ignored in the counts but kept in the registered subgraph. Works on subgraphs produced by other tools (for example the output of `filter_nodes`).

## Errors
- Unknown graph, or unknown / non-string node (use `lookup_node`).
- `direction` not one of `both`, `out`, `in`.
- `top_k` not a whole number from 1 to 100.
- Unknown parameter names.

A node with no neighbours is **not** an error: the ego network is the node alone (1 node, 0 edges).
