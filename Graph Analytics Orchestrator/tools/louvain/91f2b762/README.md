# louvain

**Author:** 91f2b762 · **Tier:** hard · **Category:** community

## What it computes
Communities found by maximising modularity with the Louvain algorithm (Blondel et al., 2008), written from scratch. It repeats two phases:

1. **Local moving.** Visit the nodes in a seeded random order. Move each node to the neighbouring community that raises modularity most (the gain of joining community C is `k_i,in(C) - resolution * tot(C) * k_i / 2m`), until a full sweep makes no move.
2. **Aggregation.** Merge each community into a single super-node (edges between communities are summed, edges inside become a self-loop) and run phase 1 again on this smaller graph.

It stops when a level no longer improves modularity. Cost is roughly O(E) per sweep and the number of nodes shrinks fast at each level; `airports` (500 nodes, 20,058 edges) takes about 0.1 s. Ties are broken by community id, and the only randomness is the node order, fixed by `seed`.

## When to use it
- "What are the communities in this network, and how strong are they?"
- "Which group does Valjean belong to?" (pass `node`)

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| top_k | integer | 10 | How many of the largest communities to return (1 to 100) |
| seed | integer | 0 | Seed for the random node order |
| resolution | number | 1.0 | Modularity resolution, greater than 0. Higher gives more, smaller communities |
| use_weights | boolean | true | Use edge weights as connection strength (weighted graphs only). Use `false` for `airports`, whose weights are distances in km |
| node | string | none | Optional node id: also report the community of that node |

## Output
`result` holds the modularity, the community count and the `top_k` largest communities (largest first, ties by smallest node id):

```json
{"modularity": 0.41979, "num_communities": 4, "num_nodes": 34,
 "communities": [
   {"community": 1, "graph_id": "karate~1", "size": 12,
    "members": [{"id": "m10", "label": "Member 10"}, "..."]}],
 "node_community": {"node": {"id": "m34", "label": "Member 34"}, "community": 2, "graph_id": "karate~2", "size": 11}}
```

Every returned community is registered in the store as a subgraph; its id is in `graph_id`, so another tool can run on it. `result_graph_id` is the id of the largest community. `members` lists a few nodes per community (fewer when `top_k` is large) so the response stays under 8 KB; use the `graph_id` for the full member list. `node_community` appears only when `node` is given.

## Graphs it supports
Undirected graphs, weighted or unweighted. Directed graphs are accepted but treated as undirected (an edge exists if either direction does; for a pair joined both ways the smaller weight is used), and the summary says so. Isolated nodes become singleton communities.

## Errors
- Unknown `graph_id`: use `list_graphs`.
- `top_k` outside 1 to 100, `seed` not an integer, `resolution` not greater than 0, `use_weights` not a boolean.
- `node` not in the graph: the error says to use `lookup_node`.
- A graph with no nodes, or no edges, or negative edge weights.
- Any unexpected extra parameter.
