# shortest_path_unweighted

**Author:** f28f69d7 · **Tier:** easy · **Category:** paths

## What it computes

Breadth-first search finds a path with the fewest edges from `source` to `target`. Neighbors are visited by ascending node ID, so equal-length paths have a consistent result. Search takes O(V + E) before neighbor sorting; sorting adds at most O(E log V).

## When to use it

Use it for questions such as “What is the fewest flights from Chennai to Delhi?” or “How many friendship links connect these two members?” It counts hops, not distance or edge weight.

## Parameters

| Name | Type | Meaning |
| --- | --- | --- |
| `graph_id` | string | Graph ID |
| `source` | string | Starting node ID |
| `target` | string | Destination node ID |

## Output

`result.path` is an ordered list of `{id, label}` nodes, and `result.hops` is the number of edges. For example, a direct route has two nodes and one hop. `result_graph_id` is null.

## Graphs it supports

Directed and undirected graphs, whether weighted or unweighted. Directed paths follow edge direction; weights are ignored. A node can reach itself in zero hops.

## Errors

Unknown graph IDs, unknown node IDs, extra parameters, unreachable destinations, and paths too large for the 8 KB output limit return an error with guidance.
