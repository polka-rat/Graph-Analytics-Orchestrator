# louvain

**Author:** f28f69d7 · **Tier:** hard · **Category:** community

## What it computes

Louvain is a modularity optimization heuristic. Each node starts in its own community. The tool repeatedly moves nodes when that improves modularity, then combines communities into weighted supernodes and repeats. A fixed `seed` controls visit order. It finds useful groups but does not guarantee the globally best modularity.

## When to use it

Use it to ask which natural groups exist in a friendship, character, or route network and how strongly separated those groups are. Each returned community is also registered as a subgraph for another tool to analyze.

## Parameters

| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| `graph_id` | string | required | Graph ID |
| `resolution` | number | 1.0 | Positive modularity resolution |
| `seed` | integer | 0 | Node visit order seed |
| `top_k` | integer | 10 | Maximum communities returned, 1 to 100 |

## Output

`result.modularity` is the partition modularity rounded to six places, and `result.total_communities` is the number found. `result.communities` is sorted by size (then smallest node ID); each entry has its full `size`, a registered `graph_id`, and labeled `nodes`. The member list may be shortened to keep the response under 8 KB; the registered subgraph still contains every member. `result_graph_id` is the largest community's subgraph ID.

## Graphs it supports

Directed and undirected graphs, weighted or unweighted. Undirected edges count in both directions internally, matching standard weighted modularity. Edge weights are interpreted as connection strength. For the airports dataset, weights are distances in kilometers, so weighted communities reflect those numbers rather than route frequency. Graphs without positive edge weight return singleton communities with modularity zero.

## Errors

Unknown graph IDs, extra parameters, invalid `resolution`, `seed`, or `top_k`, and negative or non-finite edge weights return helpful errors.
