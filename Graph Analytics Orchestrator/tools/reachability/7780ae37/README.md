# reachability

**Author:** 7780ae37 | **Tier:** easy | **Category:** paths

Answers "is there any path from A to B?" with a yes/no, the number of hops and one shortest path.

## Parameters
| name | type | description |
| --- | --- | --- |
| `graph_id` | string | graph to analyse |
| `source` | string | node id where the path starts |
| `target` | string | node id where the path should end |

## Algorithm
Breadth-first search from `source`, following `out_neighbors` (so edge direction is respected on directed graphs). It stops as soon as `target` is found. Neighbours are visited in sorted id order, so the returned path is deterministic. Parents are recorded and the path is rebuilt backwards from `target`. Complexity O(V + E) time, O(V) memory.

## Output
```json
{"status": "ok",
 "result": {"reachable": true, "hops": 2,
            "source": {"id": "m1", "label": "..."}, "target": {"id": "m34", "label": "..."},
            "path": [{"id": "m1", "label": "..."}, {"id": "m9", "label": "..."}, {"id": "m34", "label": "..."}]},
 "summary": "Yes: ... can reach ... the shortest route takes 2 hops.",
 "result_graph_id": null, "error": null}
```
Unreachable pairs are a valid answer (`reachable: false`, `hops: null`, empty `path`), not an error. Paths longer than 50 nodes are truncated (`path_truncated: true`); `hops` is always exact.

## Edge cases
- Unknown graph, or unknown `source`/`target` returns an error that points to `lookup_node`.
- `source == target` is reachable in 0 hops.
- Unknown extra parameters return an error.
- On directed graphs `A -> B` reachable does not imply `B -> A` reachable.
