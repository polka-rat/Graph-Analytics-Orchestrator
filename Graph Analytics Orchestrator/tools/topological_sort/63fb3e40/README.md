# topological_sort

**Author:** 63fb3e40 · **Tier:** medium · **Category:** paths

## What it computes
An order of a directed acyclic graph's nodes in which every edge A->B puts A before B, using Kahn's
algorithm. The graph is peeled into stages: stage 1 is the nodes with no incoming edges, stage 2 the
nodes whose predecessors are all in stage 1, and so on (the same grouping as NetworkX's
`topological_generations`). Nodes are listed by stage, then by id, so the order is deterministic.
The number of stages is the length of the longest dependency chain, i.e. the minimum number of
rounds (semesters) needed when everything in a stage can be done in parallel.

If some nodes can never be freed, the graph has a cycle and no order exists. The tool then walks
backwards from the smallest blocked node until it repeats a node (which must lie on a cycle) and runs
a breadth-first search from it to return a shortest cycle through that node.

With `node`, only that node and its ancestors (everything that must come before it) are ordered.

Time complexity is O(n log n + m).

## When to use it
Questions about dependency order or prerequisites in a directed graph:
- "In what order should I take these courses?"
- "What do I need to take before Deep Learning, and how many semesters will it take at minimum?"
- "Does this dependency graph have a cycle?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the directed graph |
| node | string | none | If given, order only this node and its ancestors; the node comes last |
| top_k | integer | 100 | How many nodes of the order to list (1 to 100); the counts always cover every node |

## Output
For a DAG, `result` is an object:

```json
{"graph_id": "courses", "is_dag": true, "target": {"id": "CS402", "label": "Deep Learning"},
 "number_of_nodes": 9, "number_of_stages": 5, "stage_sizes": [3, 3, 1, 1, 1],
 "order": [{"id": "CS101", "label": "Programming Basics", "position": 1, "stage": 1}, "...",
           {"id": "CS402", "label": "Deep Learning", "position": 9, "stage": 5}],
 "returned": 9, "truncated": false}
```

`target` is null when no `node` is given. If the order is longer than `top_k`, or would push the
response past 8 KB, only its start is listed, `truncated` is true and the summary says so.

For a graph with a cycle, `result` is still a successful result (the question was answered: no
order exists), with the cycle instead of an order:

```json
{"graph_id": "airports", "is_dag": false, "target": null, "number_of_nodes": 500, "blocked_nodes": 500,
 "cycle_length": 2, "cycle": [{"id": "ABJ", "label": "Port Bouet Airport", "position": 1},
                              {"id": "ACC", "label": "Kotoka International Airport", "position": 2}],
 "cycle_truncated": false}
```

The cycle runs from each node to the next and from the last back to the first. `blocked_nodes`
counts the nodes on or after a cycle, which cannot be placed in any order.

It does not return a subgraph (`result_graph_id` is null).

## Graphs it supports
Directed graphs, weighted or unweighted (weights are ignored). Undirected graphs return an error,
since a topological order is defined only for directed graphs. Works on registered subgraphs too.

## Errors
- Unknown `graph_id`: use list_graphs to see the available graphs.
- The graph is undirected.
- The graph has no nodes (e.g. an empty registered subgraph).
- `node` is not a node of the graph: use lookup_node to find ids.
- `top_k` not a whole number from 1 to 100.
- Unknown parameters.
