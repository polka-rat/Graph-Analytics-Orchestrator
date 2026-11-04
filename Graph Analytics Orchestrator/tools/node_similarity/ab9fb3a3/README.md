# Node similarity

Author: ab9fb3a3 · Tier: easy · Category: structure

Computes common neighbours and Jaccard similarity using set intersection and union. The denominator includes every distinct neighbour of either input node. Empty unions score 0.0; a node compared to itself scores 1.0 unless isolated. Weights and self-loops are ignored. Time and space are O(d(a) + d(b)); sorting the common neighbours adds O(c log c).

Use for: “Do these people have similar friends?” or “How many destinations do Chennai and Delhi share?”

| Parameter | Default | Meaning |
| --- | --- | --- |
| graph_id | required | Registered graph ID |
| node_a, node_b | required | Exact node IDs, resolved with lookup_node |
| direction | all | all: ignore direction; in: predecessors; out: successors |
| top_k | 10 | 1–100 common neighbours to display |

Supports directed, undirected, weighted and unweighted graphs. The direction choices are equivalent for undirected graphs.

`result` contains `node_a`, `node_b`, `direction`, `common_neighbor_count`, `union_neighbor_count`, `jaccard_score`, `common_neighbors` and `truncated`. Nodes have id and label. Common neighbours sort by ascending ID. Counts and score use all neighbours even if the display is truncated. Returns no result subgraph.

For sets {x,y} and {y,z}, the count is 1, union size 3, and score 0.333333.

Errors: unknown graph, missing/unknown node (use lookup_node), unsupported direction, invalid top_k, unknown parameters or a response exceeding 8 KB. Reduce top_k for oversized responses.

```sh
.venv/bin/python run_tool.py registry/tools/node_similarity/ab9fb3a3 graph_id=karate node_a=m1 node_b=m2
.venv/bin/python -m pytest registry/tools/node_similarity/ab9fb3a3/tests
```
