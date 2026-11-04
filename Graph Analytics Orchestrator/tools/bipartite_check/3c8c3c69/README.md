# bipartite_check

Author: 3c8c3c69 | Tier: medium | Category: structure

## What it computes
Whether the nodes can be split into two sides so that every edge goes between the sides. It colours each connected part with two colours using breadth-first search. If an edge joins two nodes of the same colour, the graph is not bipartite, and the tool returns an odd cycle as proof.

Time complexity: O(V + E).

## When to use it
- "Can the nodes be split into two groups with no links inside a group?"
- "Is the student-project network two-sided, and who is on each side?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| top_k | integer | 10 | How many nodes of each side to list (1 to 100) |

## Output
If the graph is bipartite:
- is_bipartite: true
- components: number of separate parts
- sides: side A and side B, each with its size, graph_id and the first top_k nodes by id
- sides_match_attribute: shown when a node attribute separates the two sides

result_graph_id is the larger side.

Example (projects):

```
{"is_bipartite": true, "components": 2,
 "sides": [{"side": "A", "size": 16, "graph_id": "projects~1", "nodes": [...]},
           {"side": "B", "size": 10, "graph_id": "projects~2", "nodes": [...]}],
 "sides_match_attribute": {"attribute": "side", "A": "student", "B": "project"}}
```

If the graph is not bipartite:
- is_bipartite: false
- odd_cycle and odd_cycle_length

result_graph_id is the odd cycle.

The sides follow the same rule as networkx.bipartite.color. Isolated nodes go on side B. If the graph has more than one part, the split is not unique, and the summary says so.

## Graphs it supports
- Undirected and directed graphs. Direction is ignored.
- Weighted and unweighted graphs. Weights are ignored.
- Disconnected graphs and isolated nodes.

## Errors
- Unknown graph_id
- Graph has no nodes
- top_k is not between 1 and 100
- Unknown extra parameter

A graph that is not bipartite is not an error: the tool returns is_bipartite false with the odd cycle.
