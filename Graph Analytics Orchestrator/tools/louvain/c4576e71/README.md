# louvain

**Author:** c4576e71 · **Tier:** hard · **Category:** community

## What it computes
Communities found by the Louvain method: nodes are moved greedily between communities while modularity gains are positive, then each community becomes a single node and the process repeats. Directed graphs use directed modularity; edge weights are used when present; `resolution` is the usual modularity resolution parameter. The run is repeated with five consecutive seeds (`seed` to `seed + 4`) and the partition with the best modularity is kept, so the output is deterministic for a given seed. Each level costs about O(E) per sweep.

## When to use it
- "What are the natural groups in this network?"
- "How strong is the community structure?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| resolution | number | 1.0 | Larger gives more, smaller communities |
| seed | integer | 0 | Seed for the node visiting order |
| top_k | integer | 10 | How many of the largest communities to return (1 to 100) |

## Output
`result` is a list of communities, largest first (ties by smallest member id). Each has `community` (0 is the largest), `size`, `graph_id` (a registered subgraph holding all its nodes), `members` (up to three best-connected nodes with id, label and degree) and `partition_modularity` (modularity of the whole partition, at resolution 1). `result_graph_id` is the largest community. The summary gives the total number of communities. If the response would exceed 8 KB, member samples and then the smallest communities are dropped.

## Graphs it supports
Directed and undirected, weighted or unweighted.

## Errors
- Unknown graph id.
- A graph with no nodes or no edges.
- `top_k` outside 1 to 100, `resolution` not positive, `seed` not an integer.
- Unknown extra parameter.
