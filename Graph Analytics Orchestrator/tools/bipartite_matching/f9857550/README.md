# bipartite_matching

**Author:** f9857550 (Cheripelly Karthik) · **Tier:** hard · **Category:** structure

## What it computes
A maximum matching (largest set of edges with no shared node) of an undirected bipartite graph, using Hopcroft–Karp:
1. Split nodes into left/right: from `side_attribute` if given, else by BFS 2-colouring (which also detects odd cycles, i.e. non-bipartite graphs).
2. Each phase: BFS from all free left nodes builds layers of shortest alternating paths; then an iterative DFS along those layers finds a maximal set of vertex-disjoint shortest augmenting paths and flips them.
3. Stop when the BFS finds no free right node.

Time O(E·√V). Nodes and neighbours are processed in sorted id order, so the output is deterministic.

## When to use it
- "What is the best assignment of students to projects?"
- "How many students can get a distinct project, and who is left out?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of an undirected bipartite graph |
| top_k | integer | 10 | How many matched pairs to list (1 to 100) |
| side_attribute | string | none | Node attribute with exactly two values giving each node's side, e.g. `side` |
| left_value | string | first value alphabetically | Value of `side_attribute` that marks the left side, e.g. `student` |

## Output
On `projects` with default settings (left side = the 2-colour class of the smallest node id, here the projects):
```json
{"matching_size": 9, "left_side_size": 10, "right_side_size": 16,
 "unmatched_left": 1, "unmatched_right": 7, "is_perfect": false,
 "pairs": [{"left": {"id": "P01", "label": "Project 01"}, "right": {"id": "S05", "label": "Student 05"}}],
 "pairs_truncated": true}
```
No `result_graph_id`.

## Graphs it supports
Undirected, bipartite graphs (e.g. `projects`). Weights are ignored (this is maximum-cardinality matching).

## Errors
- Directed graph → needs an undirected bipartite graph.
- Not bipartite → names an edge on an odd cycle.
- No edges.
- `side_attribute` missing on some node, not exactly two values, or an edge inside one side; `left_value` not a value of it, or given without `side_attribute`.
- Unknown `graph_id`, bad `top_k`, unknown extra parameter.
