# connected_components (e2346c64)

Finds the connected components of a graph with breadth-first search and reports their sizes.

- **Undirected graphs:** ordinary connected components.
- **Directed graphs:** weakly connected components (edge directions ignored), matching
  `networkx.weakly_connected_components`. Use `strongly_connected_components` when direction matters.

## Parameters
| name | type | default | meaning |
| --- | --- | --- | --- |
| `graph_id` | string | required | graph to analyse |
| `top_k` | integer | 10 (max 100) | how many of the largest components to list |
| `node` | string | none | also report the component containing this node |

## Output
`result` holds `num_components`, `largest_size`, `isolated_nodes`, `mode` and `components`: the
`top_k` largest, each with `rank`, `size`, `fraction`, `graph_id` (registered subgraph) and a
sample of `members` (the sample shrinks if needed to keep the output under 8 KB).
`result_graph_id` is the largest component.

Components are ordered by size, largest first; ties go to the component with the smaller
smallest node id. Members are sorted by id.

## Algorithm
Iterative BFS from each unvisited node (in sorted order), using `undirected_neighbors`.
O(V + E): well under a second on `airports`.

## Errors
Unknown graph, unknown node, bad `top_k`, unknown parameter, or an empty graph return
`status: "error"` with a message saying how to fix the call.

## Tests
`python -m pytest registry/tools/connected_components/e2346c64/tests`
