# k_hop_neighborhood

**Author:** e7c02e9e · **Tier:** easy · **Category:** subgraph (returns `result_graph_id`)

## What it computes
All nodes whose shortest-path distance (in edges, ignoring weights) from a start node is at most `k`,
found with a breadth-first search that stops at depth `k`. Time O(V + E), memory O(V).
The start node and everything found are registered in the store as an induced subgraph, so any other tool can run on it.

## When to use it
- "Who is within two hops of Member 1?"
- "Which airports can I reach from Chennai with at most one connection?" (`k=2`, `direction=out`)
- "Show me the neighbourhood around X" before running another tool on that part of the graph.

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| node | string | (required) | Id of the start node (use `lookup_node` to turn a name into an id) |
| k | integer | 2 | Maximum number of hops, 0 or more. `k=0` gives the start node alone |
| direction | string | `out` | Directed graphs only: `out`, `in` or `both`. Ignored on undirected graphs |
| top_k | integer | 10 | How many of the nearest nodes to list (1 to 100) |

## Output
`result` is a dict:
```json
{"center": {"id": "m1", "label": "Member 1 (instructor)"}, "k": 2, "edges_followed": "undirected",
 "count": 33, "hop_counts": {"1": 16, "2": 17}, "subgraph_nodes": 34, "subgraph_edges": 78,
 "nodes": [{"id": "m10", "label": "Member 10", "hops": 1}], "truncated": true}
```
- `count` is the number of nodes within `k` hops **not counting the start node**; the subgraph has `count + 1` nodes.
- `nodes` lists the nearest `top_k` nodes, ordered by hop distance then node id.
- `result_graph_id` is the induced subgraph: the start node, every node within `k` hops, and all edges among them.

## Graphs it supports
Directed and undirected, weighted or not (weights are ignored). On directed graphs `direction` chooses which
edges are followed: `out` (default, like NetworkX `single_source_shortest_path_length`), `in`, or `both`.

## Errors (all returned as `status: "error"`, never raised)
- unknown `graph_id`; unknown `node` (the message says to use `lookup_node`)
- `k` negative, fractional or not a number; `direction` not one of out/in/both; `top_k` outside 1 to 100
- an unrecognised parameter name
