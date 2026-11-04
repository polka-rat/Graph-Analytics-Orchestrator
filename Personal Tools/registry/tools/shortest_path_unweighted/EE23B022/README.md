# shortest_path_unweighted

**Author:** EE23B022 · **Tier:** Easy · **Category:** Paths

## What it computes

Finds a shortest path by number of edges between a source node and a destination
node using breadth-first search (BFS). The returned path has the fewest hops (edge
weights are ignored if present). BFS runs in O(V + E) time with respect to the
nodes and edges explored.

## When to use it

Use this tool when the question is about the fewest connections or transfers between
two known nodes. For example:

1. What is the fewest-hop route from JFK to LAX in the airport network?
2. How can Member 1 reach Member 34 through the fewest friendship links?

## Parameters

| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| `graph_id` | string | required | ID of the graph to analyse. |
| `src` | string | required | ID of the node where the path starts. |
| `dest` | string | required | ID of the node where the path ends. |

## Output

`result` is an ordered list of node references, beginning with `src` and ending with
`dest`. Each reference contains the node `id` and display `label`. The number of
edges in the path is stated in `summary`; `result_graph_id` is always `null`.

```json
{
  "status": "ok",
  "result": [
    {"id": "m1", "label": "Member 1 (instructor)"},
    {"id": "m3", "label": "Member 3"},
    {"id": "m34", "label": "Member 34 (administrator)"}
  ],
  "summary": "Shortest path from 'm1' to 'm34' is 2 edges long.",
  "result_graph_id": null,
  "error": null
}
```

## Graphs it supports

Supports directed and undirected graphs. On directed graphs, paths follow the edge
direction. It also accepts weighted graphs, but treats every edge as one hop rather
than using its weight.

## Errors

The tool returns an error when:

1. `graph_id` is missing, is not a string, or does not identify an available graph.
   Use `list_graphs` to find a valid graph ID.
2. `src` or `dest` is missing or is not a node in the selected graph. Use
   `lookup_node` to find valid node IDs.
3. An unsupported parameter is supplied. Use only `graph_id`, `src`, and `dest`.
4. No directed or undirected path exists from `src` to `dest`. Choose nodes that are
   connected in the required direction.
