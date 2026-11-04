# ego_network

**Author:** d35c782d · **Tier:** easy · **Category:** subgraph

## What it computes
Builds the ego network of one node: the node itself (the ego) and the nodes it is connected to (its neighbours, or alters), together with the edges around them. A breadth-first search from the ego collects the neighbours (and, at level 2.0, the neighbours of the neighbours), and the matching subgraph is registered in the store. Time complexity is O(n + m) for the subgraph registration plus O(sum of the degrees of the neighbours) for the search and the optional measures.

Three levels are available:
- **1.0**: the ego, its neighbours and only the edges between the ego and them.
- **1.5** (default): also the edges among the neighbours. For out-links this is the same as `networkx.ego_graph(G, node, radius=1)`.
- **2.0**: also the neighbours of the neighbours, with every edge among the chosen nodes (like `radius=2`).

Optional extras:
- **alter density**: the edges that exist among the neighbours divided by the edges that could exist (k(k-1)/2 for undirected graphs, k(k-1) for directed graphs). On undirected graphs it equals the ego's clustering coefficient.
- **neighbour groups** (when the ego is left out): the number of separate groups the neighbours form among themselves, with direction ignored. More than one group means the ego is the only link between them (a broker or bridge).

## When to use it
Use it to look at the neighbourhood around one node and to get a subgraph other tools can analyse next.
- "Show me Bob's immediate network."
- "Who is within two hops of Chennai airport, and how connected are its direct destinations?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| node | string | (required) | Node id of the ego (use `lookup_node` to find it from a name) |
| level | number | 1.5 | 1.0, 1.5 or 2.0 (see above) |
| direction | string | "out" | `out`, `in` or `both`: which links make a node a neighbour (directed graphs only; ignored on undirected graphs) |
| include_ego | boolean | true | Keep the ego node in the subgraph. If false, the result also reports the neighbour groups |
| alter_density | boolean | false | Also compute the alter density |
| top_k | integer | 10 | How many nodes to list in `result` (1 to 100). The registered subgraph always holds all nodes |

## Output
`result` is an object:
- `ego`: the ego as `{id, label}`.
- `level`, `n_nodes`, `n_edges`, `n_neighbors`: the level used and the size of the subgraph and of the neighbour set.
- `nodes`: up to `top_k` nodes, each `{id, label, distance}`, ordered by distance from the ego and then by node id. The list is shortened further if the output would pass 8 KB.
- `alter_density`: only when requested (null if there are fewer than 2 neighbours).
- `alter_components`: only when `include_ego` is false: `{count, largest_sizes}` (up to the 5 largest groups).

The full subgraph is registered and its id is returned in `result_graph_id`, so another tool can run on it.

Example (`graph_id=karate node=m1 top_k=3 alter_density=true`):
```json
{"status": "ok",
 "result": {"ego": {"id": "m1", "label": "Member 1 (instructor)"}, "level": 1.5,
            "n_nodes": 17, "n_edges": 34, "n_neighbors": 16,
            "nodes": [{"id": "m1", "label": "Member 1 (instructor)", "distance": 0},
                      {"id": "m11", "label": "Member 11", "distance": 1},
                      {"id": "m12", "label": "Member 12", "distance": 1}],
            "alter_density": 0.15},
 "summary": "Ego network of Member 1 (instructor) (m1), level 1.5: 17 nodes and 34 edges, 16 direct neighbours; showing 3 nodes. Alter density is 0.15.",
 "result_graph_id": "karate~1", "error": null}
```

## Graphs it supports
Directed and undirected graphs, weighted or not. Edge weights are ignored, since only the structure matters. On directed graphs `direction` decides which links count (outgoing by default); the subgraph keeps every edge among the chosen nodes, whichever way it points. At level 1.0 only the ego's own links are kept.

## Errors
- Unknown `graph_id`: no such graph (use `list_graphs`).
- Unknown parameter name.
- `node` missing, or not a node of the graph (use `lookup_node`).
- `top_k` is not a whole number from 1 to 100.
- `level` is not 1.0, 1.5 or 2.0.
- `direction` is not `out`, `in` or `both`.
- `include_ego` or `alter_density` is not true/false.
- `level` 1.0 with `include_ego` false: that subgraph would have no edges.
- The node has no neighbours and `include_ego` is false: the ego network would be empty.

