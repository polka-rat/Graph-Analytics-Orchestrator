# articulation_points_bridges

Author: f6f61ae0 | Tier: medium | Category: structure

Finds articulation points and bridges: vertices or edges whose removal increases the number of connected components. Use to identify single points of failure in an undirected network. Supports weighted and unweighted undirected graphs, ignoring weights; rejects directed graphs. Returns sorted node and edge references, full counts and a truncation flag, with up to top_k entries per list.

## Parameters

| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | required | ID of the graph to analyse. |
| top_k | integer | 10 | Maximum entries per result list; byte limit may reduce this further. |

## Algorithm and complexity
An iterative Tarjan DFS records discovery times and low-link values. A non-root
vertex is a cut vertex when a child's low-link is at least its discovery time.
A DFS root needs two children. A tree edge is a bridge when its child's low-link
is strictly greater than its parent's discovery time. Iteration avoids recursion
limits on long chains. Every disconnected component is explored; self-loops
are never bridges. Weights are ignored. Directed graphs are rejected because
strong and weak cuts have different meanings.
DFS costs O(V + E) time and O(V + E) auxiliary space including returned bridges;
deterministic sorting adds O(V log V + E log E) in the worst case.

## Example questions
- Which club members are single points of failure in the friendship network?
- Which student-project links disconnect part of the network if removed?

## Output
`result` has `articulation_points` (node references), `bridges` (objects with
`source` and `target` node references), `articulation_point_count`, `bridge_count`,
and `truncated`. Full counts are computed before truncating. Each list is
lexicographically sorted by ID; bridge endpoints are in ascending ID order.
Each list has at most top_k entries; long labels may shorten lists further to
stay under 8 KiB. An empty graph returns empty lists and zero counts.
`result_graph_id` is null.

## Errors
Unknown/invalid graph ID, directed graph, unknown parameter, or non-integer,
boolean, or out-of-range top_k returns a helpful contract error.

## Verification

```bash
python -m graphkit.validate registry/tools/articulation_points_bridges/f6f61ae0
python -m pytest registry/tools/articulation_points_bridges/f6f61ae0/tests
```

Tests use NetworkX only as an independent reference; runtime code uses the standard library and graphkit.
