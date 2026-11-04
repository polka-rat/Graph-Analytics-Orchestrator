# bipartite_check

**Author:** 6e31812a · **Tier:** medium · **Category:** structure

## What it computes
Whether the nodes can be split into two groups (sides A and B) so that every edge joins the two groups. It 2-colours the graph by breadth-first search: each connected component starts from its smallest node id on side A, and every neighbour gets the opposite side. The graph is bipartite exactly when no edge joins two nodes of the same side. If such an edge (u, v) is found, the BFS-tree paths from u and v to their lowest common ancestor, plus the edge itself, form an **odd cycle**, which is returned as proof that no split exists (a graph is bipartite if and only if it has no odd cycle). Time O(V + E).

## When to use it
- "Can the nodes be split into two groups with no links inside a group?"
- "Is the projects network really two-sided (students and projects)?" / "Can this graph be coloured with two colours?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| top_k | integer | 10 | How many example nodes to list per side, or of the odd cycle (1 to 100) |

## Output
If bipartite:

```json
{"is_bipartite": true, "components": 2, "edges": 28,
 "sides": [{"side": "A", "size": 10, "graph_id": "projects~1", "sample": [{"id": "P01", "label": "Project 01"}, "..."], "sample_truncated": false},
           {"side": "B", "size": 16, "graph_id": "projects~2", "sample": ["..."], "sample_truncated": true}]}
```

Each side is registered as a subgraph (its `graph_id`), and `result_graph_id` is the larger side. When the graph has several components the split is not unique; this tool always puts the smallest id of each component on side A.

If not bipartite:

```json
{"is_bipartite": false, "odd_cycle_length": 3,
 "odd_cycle": [{"id": "m11", "label": "Member 11"}, {"id": "m1", "label": "Member 1 (instructor)"}, {"id": "m5", "label": "Member 5"}],
 "odd_cycle_truncated": false, "odd_cycle_graph_id": "karate~1"}
```

The odd cycle is registered as a subgraph and returned as `result_graph_id`.

## Graphs it supports
Undirected and directed graphs; on a directed graph edge directions are ignored, as in `networkx.is_bipartite`. Weights are ignored. A self-loop makes a graph non-bipartite (odd cycle of length 1). A single node or a graph with no edges is bipartite.

## Errors
- Unknown `graph_id` → use `list_graphs`.
- Unknown parameter → the error lists the accepted ones.
- `top_k` not a whole number from 1 to 100.
- A graph with no nodes.
