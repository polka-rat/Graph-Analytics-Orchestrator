# reachability

Author: f6f61ae0 | Tier: easy | Category: paths

Checks whether any path exists from source to target using breadth-first search. Use for questions such as whether one airport can reach another. Supports directed and undirected, weighted and unweighted graphs; follows outgoing edges and ignores weights. Returns source and target node references and a reachable boolean; a node reaches itself.

## Parameters

| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | required | ID of the graph to analyse. |
| source | string | required | Starting node ID; resolve names with lookup_node. |
| target | string | required | Destination node ID; resolve names with lookup_node. |

## Algorithm and complexity
Breadth-first search follows outgoing adjacency and stops once the target is discovered.
Time O(V + E), auxiliary space O(V). A zero-edge path makes source == target reachable.
Disconnected nodes return reachable=false, not an error.

## Example questions
- Can Chennai reach Lisbon through any sequence of routes?
- Can member m1 reach member m34 through friendships?

## Output
`result` contains `source`, `target` (each an ID/label object), and `reachable`.
For example: `{"source":{"id":"a","label":"A"},"target":{"id":"b","label":"B"},"reachable":true}`.
No path is returned and `result_graph_id` is null.

## Errors
Unknown/non-string graph ID, missing/invalid node IDs (including empty graphs),
unknown parameters, or labels too long for the 8 KiB output limit return a contract error.

## Verification

```bash
python -m graphkit.validate registry/tools/reachability/f6f61ae0
python -m pytest registry/tools/reachability/f6f61ae0/tests
```

Tests use NetworkX only as an independent reference; runtime code uses the standard library and graphkit.
