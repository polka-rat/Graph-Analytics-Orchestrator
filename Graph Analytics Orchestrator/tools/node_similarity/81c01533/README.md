# TODO_tool_name

**Author:** 81c01533 · **Tier:** Easy · **Category:** Structure

## What it computes

Computes the Jaccard similarity coefficient and common neighbor count between two nodes in a graph. For directed graphs, it compares their sets of outgoing neighbors; for undirected graphs, it compares their full neighbor sets. Time complexity is O(d1 + d2), where d1 and d2 are the degrees of the two input nodes.

## When to use it

Use this tool to evaluate structural similarity or overlap between two specific entities in a network based on shared connections.

Example questions:

- "How similar are user_A and user_B based on the accounts they follow?"
- "How many common connections do node1 and node2 share, and what is their similarity score?"

## Parameters

| Name | Type | Default | Meaning |
|------|------|---------|---------|
| `graph_id` | string | (required) | Id of the graph |
| `node1` | string | (required) | ID of the first node to compare |
| `node2` | string | (required) | ID of the second node to compare |

## Output

Returns a dictionary containing `common_neighbours` (integer count of shared outgoing/adjacent neighbors) and `jaccard_score` (float ranging from 0.0 to 1.0).

Example:

```json
{
  "result": {
    "common_neighbours": 3,
    "jaccard_score": 0.375
  },
  "summary": "nodeA and nodeB have 3 and a jaccard similarity score of 0.375"
}
```

## Graphs it supports

Supports both directed and undirected graphs . For directed graphs, similarity is based solely on outgoing edges. Edge weights are ignored if present.

## Errors

- `"No graph with id '{graph_id}'"`: The specified graph ID does not exist in the store.
- `"graph_id must be a string'"`: The specified graph ID is not a string.
- `"Node '{node1}' not found in graph '{graph_id}'."`: The first input node ID is invalid or missing.
- `"Node '{node2}' not found in graph '{graph_id}'."`: The second input node ID is invalid or missing.
- `"Unknown parameter(s): {params}"`: Unrecognized parameters were passed to the function.
