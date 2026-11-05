# greedy_coloring

**Author:** f28f69d7 · **Tier:** medium · **Category:** structure

## What it computes

Nodes are visited by descending number of distinct neighbors, with node ID breaking ties. Each receives the smallest non-negative color unused by an already colored neighbor. This produces a valid coloring, though it does not promise the minimum possible number of colors. Runtime is O(V log V + E + VΔ), where Δ is the maximum degree.

## When to use it

Use it to assign conflict-free exam slots or other groups where connected nodes cannot share a slot. Color numbers start at 0 and can be treated as slot identifiers.

## Parameters

| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| `graph_id` | string | required | Graph ID |
| `top_k` | integer | 100 | Maximum assignments shown, from 1 to 100 |

## Output

`result.num_colors` is the number of colors used for the complete graph. `result.total_nodes` is its node count. `result.colors` contains up to `top_k` `{id, label, color}` assignments sorted by node ID. The list may be shorter to keep the response under 8 KB. `result_graph_id` is null.

## Graphs it supports

Directed and undirected graphs, weighted or unweighted. A directed edge is treated as a conflict between its endpoints regardless of direction; weights do not affect coloring. An empty graph uses zero colors.

## Errors

Unknown graph IDs, invalid `top_k`, extra parameters, and self-loops return an error with guidance. A self-loop cannot be properly colored.
