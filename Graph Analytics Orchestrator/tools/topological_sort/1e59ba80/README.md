# topological_sort

**Author:** 1e59ba80 · **Tier:** medium · **Category:** paths

## What it computes
An ordering of a directed acyclic graph in which every edge A→B puts A before B, or a cycle if the graph has one.

It uses Kahn's algorithm with a min-heap: it repeatedly takes the smallest-id node that has no remaining incoming edges, so ties are broken by node id and the result equals NetworkX's `lexicographical_topological_sort`. Each node also gets a level, the length of the longest prerequisite chain before it, so nodes on the same level do not depend on each other.

If some nodes are never freed, the graph has a cycle. The tool walks back from one of those nodes to a node that is on a cycle, then uses breadth-first search to return the shortest cycle through it.

Time complexity is O((V + E) log V).

## When to use it
Dependency and ordering questions on directed graphs. For example:
- "In what order should these courses be taken?"
- "Is there a circular dependency in these prerequisites?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of a directed graph |

## Output
On a DAG, `result` has `is_dag: true`, `num_nodes`, `num_levels`, `nodes_shown` and `order`, the nodes in order, each with `position` and `level`:

```json
{"is_dag": true, "num_nodes": 21, "num_levels": 5, "nodes_shown": 21,
 "order": [{"id": "CS101", "label": "Programming Basics", "position": 1, "level": 0}, "..."]}
```

On a graph with a cycle, `result` has `is_dag: false`, `cycle_length`, `cycle` (the nodes in cycle order, each with `position`; the last node links back to the first) and `num_unorderable_nodes` (the nodes on or after a cycle):

```json
{"is_dag": false, "cycle_length": 2, "num_unorderable_nodes": 500,
 "cycle": [{"id": "ABJ", "label": "Port Bouet Airport", "position": 1},
           {"id": "ACC", "label": "Kotoka International Airport", "position": 2}]}
```

It does not return `result_graph_id`. If the output would exceed 8 KB, the list is cut short and the summary says so; on the provided datasets this never happens.

## Graphs it supports
- **Directed graphs:** weighted or unweighted; weights are ignored.
- **Undirected graphs:** return an error, since every edge goes both ways and there is no order.

## Errors
- Unknown `graph_id`: use `list_graphs`.
- Any parameter other than `graph_id`.
- An undirected graph.
- A graph with no nodes.
