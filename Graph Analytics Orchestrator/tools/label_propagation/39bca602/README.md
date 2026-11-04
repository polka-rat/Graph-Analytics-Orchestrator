# label_propagation

**Author:** 39bca602 · **Tier:** medium · **Category:** community

## What it computes
Identifies dense modular groupings using semi-synchronous label propagation. Nodes initialize with distinct labels and adopt the dominant community label among their neighbors based on cumulative edge weights. Runs in near-linear time $O(m \cdot \text{max\_iter})$.

## When to use it
- "What natural communities or clusters exist in the network?"
- "Split the karate club network into cohesive subgroups."

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| `graph_id` | string | (required) | Graph identifier |
| `max_iter` | integer | 30 | Iteration limit before stopping |
| `seed` | integer | 0 | Seed for deterministic node shuffling |
| `top_k` | integer | 10 | Number of top communities to return (1 to 100) |

## Output
Returns `result_graph_id` referencing the largest registered community subgraph. Each entry in `result` contains the registered subgraph `graph_id`, community size, and sample node objects.

## Graphs it supports
Supports directed and undirected, weighted and unweighted graphs.

## Errors
- Unknown `graph_id`
- Invalid `top_k` or `max_iter`
- Unknown arguments