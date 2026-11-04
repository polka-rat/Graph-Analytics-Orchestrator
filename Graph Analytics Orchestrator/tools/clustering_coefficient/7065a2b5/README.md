# clustering_coefficient

**Author:** 7065a2b5 · **Tier:** easy · **Category:** structure

## What it computes
A node's local clustering coefficient is the fraction of pairs of its neighbours that are connected to each other. For a node of degree `d` that lies on `T` triangles:

    clustering = 2T / (d(d-1))

A value of 0 means none of its neighbours know each other. A value of 1 means they all do. Nodes with fewer than two neighbours score 0. The graph's average clustering is the mean over all nodes, zeros included.

- **Directed graphs** use the directed formula from Fagiolo (2007): `T / (d_tot(d_tot-1) - 2·d_bi)`. Here `T` counts the directed triangles of every edge orientation, `d_tot` is in-degree plus out-degree, and `d_bi` is the number of neighbours linked in both directions.
- **`weighted=true`** counts each triangle as the geometric mean of its three edge weights, each divided by the largest weight in the graph (Onnela et al., 2005).
- Self-loops are ignored.

These are the same definitions NetworkX uses in `clustering` and `average_clustering`.

The tool builds a neighbour set for every node and intersects the sets of adjacent nodes. That costs O(Σ d(v)²) time: about 0.1 s on `airports`, or about 1 s with weights.

## When to use it
Use it for questions about how tightly knit a node's neighbourhood is, or how clustered the whole network is.
- "How tightly knit is the karate instructor's circle of friends?" (`node=m1`)
- "How clustered is the airline network, and which airports have the most interconnected neighbours?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| top_k | integer | 10 | How many nodes with the highest clustering to return (1 to 100) |
| node | string | (none) | Return only this node's clustering, plus the graph average |
| weighted | boolean | false | Weigh triangles by their edge weights |

The tool accepts some inputs that LLMs often send, rather than returning an error:
- `null` means the parameter's default, and `""` for `node` means no node.
- `top_k` may be `5.0` or `"5"`, and `weighted` may be `"true"` or `"false"`.
- `node` may be a number, such as `5` for node `"5"`. Letter case and extra spaces are ignored when exactly one node matches, so `" M1 "` finds `m1`.

## Output
- **Without `node`:** `result` is a list of the `top_k` nodes, highest clustering first. Equal scores are ordered by node id. The summary gives the graph's average clustering, how many nodes share the highest value, and how many score 0.
  ```json
  [{"id": "m13", "label": "Member 13", "score": 1.0}, {"id": "m15", "label": "Member 15", "score": 1.0}, ...]
  ```
  Summary: *The average clustering of 'karate' is 0.570638 over 34 nodes. 11 nodes share the highest clustering, 1.0; 2 nodes have clustering 0.*
- **With `node`:** `result` is one object with these fields:
  - `score`
  - `degree`: neighbours, or in+out edges on a directed graph
  - `average_clustering`: the graph average
  - `triangles`: when `weighted=false`. On directed graphs this is the number of directed triangles.

  ```json
  {"id": "m1", "label": "Member 1 (instructor)", "score": 0.15, "degree": 16, "average_clustering": 0.570638, "triangles": 18}
  ```
  Summary: *Member 1 (instructor) (m1) has clustering 0.15: 18 of the 120 pairs of its 16 neighbours are linked. The average clustering of 'karate' is 0.570638 over 34 nodes.*

Scores are rounded to 6 decimals. The response stays under 8 KB. If `top_k` is close to 100 and the labels are long, the lowest-ranked entries are dropped and the summary says so.

There is no `result_graph_id`; the tool returns no subgraph.

## Graphs it supports
- **Undirected and directed graphs.** Directed graphs use the directed formula.
- **Weighted and unweighted graphs.** Weights are ignored unless `weighted=true`. Negative or non-finite weights are rejected. If every weight is 0, each triangle weighs 0, so every weighted score is 0. NetworkX crashes with a division by zero in this case; this tool does not.
- **Self-loops** are ignored. **Graphs without edges, or with a single node:** every score is 0.
- **Triangle-free graphs** (bipartite graphs such as `projects`, or `courses`): every score is 0, and the summary says the graph has no triangles.

## Errors
- `graph_id` is missing or unknown. The message suggests `list_graphs`.
- `node` is not in the graph. The message suggests `lookup_node`.
- `top_k` is not a whole number from 1 to 100.
- `weighted` is not `true` or `false`.
- A parameter is unknown.
- The graph has no nodes.
- `weighted=true` on a graph with negative or non-finite edge weights.
