# bipartite_matching

**Author:** EE23B022 · **Tier:** Hard · **Category:** Structure

## What it computes

Finds a maximum-cardinality matching in a bipartite graph using the Hopcroft-Karp
algorithm. A matching is a set of pairs in which each node appears at most once.
The algorithm runs in O(E√V) time and ignores edge weights.

## When to use it

Use this tool for one-to-one assignment problems. For example:

1. What is the largest possible assignment of students to projects?
2. Which applicants can be paired with distinct available positions?

## Parameters

| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| `graph_id` | string | required | ID of the bipartite graph to analyse. |
| `top_k` | integer | `10` | Maximum matched pairs shown in the result (1–100). |

## Output

`result.matches` contains node-reference pairs from a maximum matching. Each pair
uses generic `left` and `right` fields for the two partitions. `matching_size` is the
full cardinality of the matching, even when `top_k` truncates the displayed pairs.
`result_graph_id` is always `null`.

```json
{
  "status": "ok",
  "result": {
    "matches": [
      {
        "left": {"id": "P03", "label": "Project 03"},
        "right": {"id": "S01", "label": "Student 01"}
      }
    ],
    "matching_size": 9,
    "left_partition_name": "student",
    "right_partition_name": "project",
    "truncated": false
  },
  "summary": "Found a maximum matching of 9 pair(s) in 'projects'.",
  "result_graph_id": null,
  "error": null
}
```

## Graphs it supports

Supports bipartite graphs with or without weights. It checks bipartiteness before
matching and returns an error for graphs with an odd cycle or self-loop. Directed
graphs are treated as undirected so that an edge in either direction permits a pair.

## Errors

The tool returns an error when:

1. `graph_id` is missing, is not a string, or does not identify an available graph.
   Use `list_graphs` to find a valid graph ID.
2. The graph is not bipartite. Select a graph whose nodes can be divided into two
   groups with edges only between the groups.
3. `top_k` is not a whole number from 1 to 100. Provide an integer in that range.
4. An unsupported parameter is supplied. Use only `graph_id` and `top_k`.
