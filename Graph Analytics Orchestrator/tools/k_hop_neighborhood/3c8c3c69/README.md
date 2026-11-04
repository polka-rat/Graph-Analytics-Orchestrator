# k_hop_neighborhood

Author: 3c8c3c69 | Tier: easy | Category: subgraph

## What it computes
All nodes within k hops of a start node, using breadth-first search that stops after k levels. Each node is returned with its distance in hops. The nodes, plus the start node, are saved as a subgraph.

Time complexity: O(V + E).

## When to use it
- "Who is within two hops of Valjean?"
- "Which airports can I reach from Chennai with at most one stop?" (k = 2)

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| node | string | (required) | Id of the start node (use lookup_node to find it) |
| k | integer | 2 | Maximum number of hops, at least 1 |
| direction | string | out | Directed graphs only: out, in or both |
| top_k | integer | 10 | How many of the nearest nodes to list (1 to 100) |

## Output
- center: the start node
- k and direction used
- count: number of nodes found, not counting the start node
- per_hop: number of nodes at each distance
- nodes: the top_k nearest nodes, sorted by hops and then by id

Example (karate, node m1, k 2):

```
{"center": {"id": "m1", "label": "Member 1 (instructor)"}, "k": 2, "direction": "undirected",
 "count": 25, "per_hop": [{"hops": 1, "count": 16}, {"hops": 2, "count": 9}],
 "nodes": [{"id": "m11", "label": "Member 11", "hops": 1}, ...]}
```

result_graph_id is the subgraph of the start node and all nodes found.

## Graphs it supports
- Directed and undirected graphs. In directed graphs, out follows edges forwards, in follows them backwards and both ignores direction.
- Weighted and unweighted graphs. Weights are ignored; every edge is one hop.

## Errors
- Unknown graph_id
- node missing or not in the graph
- k is not a whole number of at least 1
- direction is not out, in or both
- top_k is not between 1 and 100
- Unknown extra parameter

If no node is within k hops, this is not an error: the tool returns count 0 and explains why.
