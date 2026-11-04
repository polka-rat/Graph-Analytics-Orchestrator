# bipartite_matching

**Author:** c52598eb · **Tier:** hard · **Category:** structure

## What it computes
A maximum-cardinality matching: the largest set of edges in which no node appears twice.

1. **Split the nodes into two sides.** If every node has a `side` attribute with exactly two values, and every edge joins the two values (as in `projects`, with sides `student` and `project`), that split is used. Otherwise the graph is 2-coloured with BFS; a clash means an odd cycle, so the graph is not bipartite. The side of the first node becomes the left side.
2. **Hopcroft–Karp.** Each phase runs a BFS from all free left nodes to build distance layers, then a DFS (iterative, so no recursion limit) that finds a maximal set of vertex-disjoint shortest augmenting paths and flips them. It stops when no augmenting path is left.

Time: O(m √n).

## When to use it
Assignment questions between two groups:
- "What is the best assignment of students to projects?" → `{"graph_id": "projects"}`
- "How many students can get a project, and how many are left out?" → same call; see the summary.

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of an undirected bipartite graph, such as `projects` |

## Output
`result` is the list of matched pairs, sorted by left node id. Each pair is `{"left": {id, label}, "right": {id, label}}`, and `len(result)` is the matching size. The summary gives the size and how many nodes on each side stay unmatched. No `result_graph_id`.

```json
{"left": {"id": "S01", "label": "Student 01"}, "right": {"id": "P03", "label": "Project 03"}}
```

On `projects` the matching has 9 pairs: 9 of the 16 students get one of 9 of the 10 projects. The response stays under 8 KB; for a very large matching only the first pairs are listed and the summary says so.

## Graphs it supports
Undirected bipartite graphs, weighted or not; weights are ignored because the matching maximises the number of pairs. Works on subgraphs registered by other tools. A graph with no edges gives an empty matching.

## Errors
- Unknown `graph_id` → use list_graphs.
- Directed graph (e.g. airports, courses) → needs an undirected bipartite graph.
- Not bipartite (e.g. karate, lesmis) → the error names an edge that closes an odd cycle.
- Unknown parameter names.
