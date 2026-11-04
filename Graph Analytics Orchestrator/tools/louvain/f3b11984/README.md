# louvain

**Author:** f3b11984 · **Tier:** hard · **Category:** community (returns subgraphs)

## What it computes
Communities by the Louvain method (Blondel et al., 2008), which greedily maximises modularity. Phase 1 visits the nodes in a seeded random order and moves each node to the neighbouring community with the best modularity gain `w(i, C) − resolution · tot(C) · k(i) / 2m`, repeating until no move helps. Phase 2 collapses every community into a single node (internal edges become a self-loop) and repeats phase 1 on the smaller graph. The loop stops when a phase-1 run makes no move. Each pass strictly raises modularity, so it terminates; in practice the cost is close to O(E) per level.

The reported modularity is `Σ_c [ in_c / 2m − resolution · (tot_c / 2m)² ]` on the weights actually used; it is the usual modularity when resolution is 1.

## When to use it
- "What natural groups exist in this network?"
- "Which community is Valjean in, and who else is in it?"
- "How strong is the community structure?" (modularity above about 0.3 is clear)

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| resolution | number | 1.0 | Larger gives more, smaller communities; smaller gives fewer, larger ones (must be > 0) |
| seed | integer | 0 | Seed of the random node order; same seed, same result |
| top_k | integer | 10 | How many of the largest communities to return (1 to 100) |
| weighted | boolean | true | Use edge weights as connection strength when the graph has them |
| node | string | none | If given, return only the community containing this node (`top_k` is then ignored) |

## Output
`result` is a list of communities, largest first (ties: the community holding the lowest-indexed node first):
```json
{"community": 1, "size": 12, "graph_id": "karate~1",
 "top_members": [{"id": "m34", "label": "Member 34 (administrator)", "degree": 17.0}, "..."]}
```
`top_members` are the five highest-degree members (weighted degree, ties by id). `graph_id` is a subgraph registered with the store holding exactly that community's nodes and the edges among them, so any other tool can run on it. `result_graph_id` is the id of the largest community (or of the requested node's community). The `summary` gives the number of communities and the modularity. If a long list would exceed 8 KB, the smallest communities are left out and the summary says so.

## Graphs it supports
Undirected and directed graphs, weighted or not. A directed graph is treated as undirected: the weights of `u→v` and `v→u` are added. `weighted=true` (the default, as in NetworkX) uses edge weights as strength of connection; on `airports` the weight is a distance in km, so pass `weighted=false` there. Isolated nodes form communities of one. Negative weights are rejected.

## Errors
- Unknown graph id (use `list_graphs`), unknown `node` (use `lookup_node`).
- `resolution` not a number above 0; `seed` not a whole number; `weighted` not a boolean; `top_k` outside 1 to 100.
- Graph with no edges, all weights zero, or negative weights.
- Unknown parameter names.
