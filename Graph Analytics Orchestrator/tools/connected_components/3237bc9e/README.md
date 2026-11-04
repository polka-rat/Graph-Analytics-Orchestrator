# connected_components

**Author:** 3237bc9e · **Tier:** easy · **Category:** community

## What it computes
The connected components of a graph: groups of nodes that can all reach each other. A breadth-first search is started from every node not yet visited, and each search collects one component. On directed graphs edge direction is ignored (weakly connected components). Time O(n + m).

## When to use it
Whether a network holds together and how it splits into separate parts.
- "Is the airport network connected?"
- "What is the largest connected part of this graph?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| top_k | integer | 10 | How many of the largest components to list (1 to 100) |

## Output
`component_count` and `components`: the `top_k` largest (ties by smallest node id), each with `rank`, `size`, `graph_id` (registered subgraph), up to 10 `members` and `more_members`. `result_graph_id` is the largest component.

```json
{"component_count": 2,
 "components": [{"rank": 1, "size": 25, "graph_id": "projects~1", "members": ["..."], "more_members": 15},
                {"rank": 2, "size": 1, "graph_id": "projects~2", "members": [{"id": "P08", "label": "Project 08"}], "more_members": 0}]}
```

## Graphs it supports
Undirected and directed (direction ignored); weights are ignored.

## Errors
Unknown `graph_id`; `top_k` not a whole number from 1 to 100; unknown parameters.
