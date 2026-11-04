# node_embedding_similarity

**Author:** efd53284 · **Tier:** hard · **Category:** structure

## What it computes
A DeepWalk-style node embedding followed by cosine similarity:

1. Generate `walks_per_node` seeded random walks of length `walk_length`.
   Walks run on the symmetrised graph, so directed edges contribute in both
   directions.
2. Count how often each pair of nodes appears within `window` steps of each
   other.
3. Convert the co-occurrence counts to a positive pointwise mutual information
   (PPMI) matrix.
4. Factorise the PPMI matrix with a symmetric eigendecomposition and keep the
   `dimensions` largest components.
5. Rank every other node by cosine similarity to the query node.

The method is deterministic for a fixed `seed`. Complexity is
O(V · walks_per_node · walk_length · window) for the walks plus O(V^3) for the
eigendecomposition, which is fast for the 500-node airports graph.

## When to use it
Structural-similarity questions:
- "Which airports have a route profile similar to Chennai?"
- "Which club members have a role like the instructor's?"

This is not a shortest-path or community-detection tool.

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| node | string | (required) | Id of the query node |
| top_k | integer | 10 | Number of similar nodes to return (1 to 100) |
| dimensions | integer | 16 | Embedding dimensions (2 to 64) |
| walk_length | integer | 20 | Nodes visited per random walk (2 to 40) |
| walks_per_node | integer | 10 | Random walks started from each node (1 to 20) |
| window | integer | 5 | Co-occurrence context window (1 to 10) |
| seed | integer | 0 | Random seed; the same seed gives the same output |

## Output
`result` is a list of node references ordered by decreasing `score`, excluding
the query node. Scores are cosine similarities in [-1, 1], rounded to six
decimal places. Ties are broken by node id ascending. `result_graph_id` is
always `null`.

The whole response must stay under 8 KB. If `top_k` is large and the labels are
long, the tool returns the largest prefix of the ranking that fits, so the list
can contain fewer than `top_k` entries. Use a smaller `top_k` to control this
explicitly.

## Graphs it supports
Directed and undirected, weighted and unweighted. Random walks use the
symmetrised neighbour set, so an A→B route and a B→A route both contribute to
the structural similarity. Edge weights do not change the walk probabilities;
walks explore graph structure, not edge magnitudes.

Disconnected graphs are supported as long as the query node has at least one
neighbour; walks stay inside the query node's component. If the query node is
isolated in the graph (or the graph has no edges), the tool returns an error
instead of an all-zero result.

## Errors
- Unknown `graph_id`.
- Unknown `node` (the error suggests `lookup_node`).
- A query node with no neighbours, so no random-walk context exists.
- Invalid `top_k`, `dimensions`, `walk_length`, `walks_per_node`, `window` or `seed`.
- A graph with fewer than two nodes.
- Unknown parameters.
