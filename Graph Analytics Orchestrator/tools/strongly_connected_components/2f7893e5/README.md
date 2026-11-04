# strongly_connected_components

**Author:** 2f7893e5 · **Tier:** medium · **Category:** community · Registers subgraphs ↪

## What it computes
The strongly connected components (SCCs) of a directed graph: the maximal groups of nodes in which every node can reach every other along edge directions. It uses **Tarjan's algorithm** in O(n + m) time. One depth-first search gives each node a discovery `index` and a `low` value, the smallest index it can reach through its DFS subtree plus one edge back into the nodes still on the stack. A node whose `low` equals its own `index` is the root of a component, and that component is popped off the stack.

The DFS is **iterative**: an explicit stack of (node, neighbour iterator) pairs replaces recursion. This means a long chain or cycle cannot overflow Python's recursion limit (the tests include a 5000-node cycle).

Components are ordered largest first; components of equal size are ordered by their smallest node id. Each returned component is registered as a subgraph in the store.

## When to use it
- "Can you fly from any airport to any other and get back again?" (is the graph strongly connected?)
- "Which courses are in a prerequisite cycle?" (on a DAG every component is a single node)
- "Which airports are mutually reachable with Chennai?" (`node="MAA"`)

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of a directed graph or registered subgraph |
| top_k | integer | 10 | How many components to list, largest first (1 to 100) |
| node | string | none | If given, return only the component that contains this node |

## Output
For the German airports (`filter_nodes` with country = Germany, registered as `airports~1`) and `top_k=2`:

```json
{"num_components": 4, "largest_size": 15, "is_strongly_connected": false,
 "components": [
   {"rank": 1, "size": 15, "graph_id": "airports~2",
    "nodes": [{"id": "BRE", "label": "Bremen Airport"}, {"id": "CGN", "label": "Cologne Bonn Airport"},
              "... 10 nodes listed in all"]},
   {"rank": 2, "size": 1, "graph_id": "airports~3",
    "nodes": [{"id": "HHN", "label": "Frankfurt-Hahn Airport"}]}
 ]}
```

- `num_components`, `largest_size` and `is_strongly_connected` describe the whole graph, not just the listed components.
- Each listed component is registered with `store.subgraph`, and its id is in `graph_id`. The subgraph holds every member and all edges among them, so other tools (e.g. `betweenness_centrality`, `graph_summary`) can run on it.
- `result_graph_id` is the first listed component: the largest one, or the one containing `node`.
- At most 10 member nodes (sorted by id) are listed per component. To keep the response under 8 KB, fewer are listed for very many components (always at least one), and in the extreme case fewer components are listed. The summary says how many were listed.

## Graphs it supports
Directed graphs only, weighted or unweighted (weights are ignored). On `airports` the whole graph is one component of 500 nodes. On `courses` (acyclic) there are 21 single-node components. Country subgraphs of `airports` (via `filter_nodes`) give more varied results.

## Errors
- Undirected graph: SCCs are not defined there; suggests `connected_components` or a directed graph from `list_graphs`.
- Unknown `graph_id`: suggests `list_graphs`.
- Unknown `node`: suggests `lookup_node`.
- `top_k` not a whole number from 1 to 100.
- Graph with no nodes (e.g. an empty registered subgraph): there are no components.
- Unknown extra parameters.
