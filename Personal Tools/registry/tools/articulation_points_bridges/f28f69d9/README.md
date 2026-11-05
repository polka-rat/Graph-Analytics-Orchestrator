# articulation_points_bridges

**Author:** EE23B022 · **Tier:** Medium · **Category:** Structure

## What it computes

Finds articulation points and bridges: nodes and edges whose removal increases the
number of connected components. The tool uses Tarjan's depth-first-search algorithm,
which runs in O(V + E) time. Edge weights do not affect this structural analysis.

## When to use it

Use this tool to identify single points of failure in a network. For example:

1. Which single airport closure would split the airport network into separate parts?
2. Which friendship links are the only connection between parts of the karate-club network?

## Parameters

| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| `graph_id` | string | required | ID of the graph to analyse. |
| `top_k` | integer | `10` | Maximum articulation points and bridges returned in each list (1–100). |

## Output

`result` contains separate lists for articulation points and bridges, plus totals for
the complete result. An endpoint of every bridge is a node reference with an `id` and
display `label`. If either list has more than `top_k` entries, `truncated` is `true`.
`result_graph_id` is always `null`.

```json
{
  "status": "ok",
  "result": {
    "articulation_points": [
      {"id": "m1", "label": "Member 1 (instructor)"}
    ],
    "bridges": [
      {
        "source": {"id": "m1", "label": "Member 1 (instructor)"},
        "target": {"id": "m2", "label": "Member 2"}
      }
    ],
    "total_articulation_points": 1,
    "total_bridges": 1,
    "truncated": false
  },
  "summary": "Found 1 articulation point(s) and 1 bridge(s) in 'karate'.",
  "result_graph_id": null,
  "error": null
}
```

## Graphs it supports

Supports both directed and undirected graphs, with or without weights. For a directed
graph, it ignores edge direction and finds failures in the underlying undirected
(weakly connected) network. Therefore, an airport route A → B is considered a
connection between A and B for this analysis.

## Errors

The tool returns an error when:

1. `graph_id` is missing, is not a string, or does not identify an available graph.
   Use `list_graphs` to find a valid graph ID.
2. `top_k` is not a whole number from 1 to 100. Provide an integer in that range.
3. An unsupported parameter is supplied. Use only `graph_id` and `top_k`.
