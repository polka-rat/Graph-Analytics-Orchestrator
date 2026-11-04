# k_hop_neighborhood

**Author:** b2eb4e3d · **Tier:** easy · **Category:** subgraph

## What it computes
Finds every node within k hops of a centre node using breadth-first search (BFS). The search expands one level per hop, and the first time a node is reached is its shortest hop distance. Time complexity is O(V + E) and memory is O(V). Edge weights are ignored, so a hop is one edge regardless of weight.

## When to use it
Use it to find who or what lies near a node, and how big that local neighbourhood is. Example questions:
- "Which airports can I reach from Chennai in at most 2 flights?"
- "Who is within 2 steps of the club's instructor in the karate network?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| node | string | best-connected node | Id of the centre node (an id, not a label; find it with `lookup_node`). If omitted, the node with the highest degree is used, ties broken by smallest id |
| k | integer | 1 | Maximum number of hops, a whole number of at least 1 |
| direction | string | out | Directed graphs only: `out` follows edges leaving a node, `in` follows edges entering it, `both` ignores direction. Ignored on undirected graphs |
| top_k | integer | 10 | How many nodes to list (1 to 100) |

## Output
`result` contains:
- `center`: the centre node as `{id, label}`
- `default_center`: true when `node` was omitted and the best-connected node was chosen
- `k` and `direction` (`"undirected"` for undirected graphs)
- `total_reached`: how many nodes are within k hops, excluding the centre
- `count_by_distance`: number of nodes at each hop distance
- `nodes`: up to `top_k` nodes, each `{id, label, distance}`, sorted by distance and then by id ascending
- `truncated`: true if `nodes` lists fewer nodes than `total_reached`

The full neighbourhood (the centre plus every node reached) is registered as a subgraph, and its id is returned as `result_graph_id`, so other tools can analyse it. Repeating the same query returns the same subgraph id. The list is also trimmed if needed to keep the output under 8 KB.

Abridged example for `graph_id=airports node=MAA k=1`:

    {"center": {"id": "MAA", "label": "Chennai International Airport"},
     "default_center": false,
     "k": 1, "direction": "out", "total_reached": 28,
     "count_by_distance": {"1": 28},
     "nodes": [{"id": "...", "label": "...", "distance": 1}, "..."],
     "truncated": true}

## Graphs it supports
Directed and undirected graphs, weighted or unweighted (weights are ignored). On a directed graph, `direction` chooses which edges to follow. On an undirected graph, `direction` has no effect.

## Errors
Every error is returned as `error(...)`, never raised:
- Unknown `graph_id`: use `list_graphs` to see the available graphs.
- `node` is given but is not a string or not in the graph: use `lookup_node` to find node ids.
- The graph has no nodes (only possible when `node` is omitted).
- `k` is not a whole number of at least 1 (booleans and strings are rejected).
- `direction` is not `out`, `in` or `both`.
- `top_k` is not a whole number from 1 to 100.
- An unknown parameter is passed.
- The neighbourhood subgraph could not be registered.