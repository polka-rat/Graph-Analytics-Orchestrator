# strongly_connected_components (e2346c64)

Finds the strongly connected components (SCCs) of a directed graph using **Kosaraju's algorithm**,
written iteratively so deep graphs cannot hit Python's recursion limit.

An SCC is a maximal set of nodes in which every node can reach every other along directed edges.

## Parameters
| name | type | default | meaning |
| --- | --- | --- | --- |
| `graph_id` | string | required | directed graph to analyse |
| `top_k` | integer | 10 (max 100) | how many of the largest SCCs to list |
| `node` | string | none | also report the SCC containing this node |

## Output
`result` holds `num_components`, `largest_size`, `singleton_components`, `nontrivial_components`
and `components` (the `top_k` largest, each with `rank`, `size`, `fraction`, `graph_id` and a
sample of `members`, shrunk if needed to stay under 8 KB). Every listed SCC is registered with
the store; `result_graph_id` is the largest.

Ordering: by size, largest first; ties go to the SCC with the smaller smallest node id. Members are sorted by id.

## Algorithm
Kosaraju's two-pass method. Pass 1: depth-first search on the graph (explicit stack of
(node, next-successor index) frames) records nodes in order of finishing time. Pass 2:
depth-first search on the reversed graph (using `in_neighbors`), starting from nodes in
decreasing finishing time; each search tree is one SCC. Nodes are visited in sorted order,
so the run is deterministic.
O(V + E).

## Errors
Undirected graph (suggests `connected_components`), unknown graph, unknown node, bad `top_k`,
unknown parameter or an empty graph all return `status: "error"`.

## Tests
`python -m pytest registry/tools/strongly_connected_components/e2346c64/tests`
