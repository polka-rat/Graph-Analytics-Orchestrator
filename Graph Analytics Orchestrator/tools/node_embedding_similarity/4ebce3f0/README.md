# node_embedding_similarity

**Author:** 4ebce3f0 · **Tier:** hard · **Category:** structure

## What it computes
DeepWalk-style node embeddings and the nodes most similar to a given node.
1. **Random walks:** from every node, `walks_per_node` uniform random walks of `walk_length` nodes, each step moving to a random neighbour (edge direction ignored).
2. **Skip-gram with negative sampling** (word2vec applied to walks), written in NumPy: each node gets a vector of length `dimensions`. Pairs of nodes within `window` steps on a walk are pulled together; 5 random "negative" nodes per pair (drawn in proportion to walk frequency^0.75) are pushed apart. Mini-batch SGD for `epochs` passes, learning rate decaying from 0.025 to 0.0001.
3. **Similarity:** cosine similarity between the query node's vector and every other node's vector.

Time is roughly proportional to V × walks_per_node × walk_length × window × dimensions × epochs: about 3–8 s on `airports` with the defaults, well under a second on the small graphs. Settings that would need more than about twice the default work on `airports` are refused with an error, so a call never approaches the 30 s limit.

## When to use it
For "which nodes play a similar role / sit in a similar place in the network?" questions, including nodes that are not directly linked. Examples:
- "Which airports are most like Chennai in the route network?"
- "How similar are Valjean and Javert's positions in Les Misérables?" (`node` = Valjean, `target` = Javert)

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| node | string | (required) | Node to find similar nodes for |
| top_k | integer | 10 | How many similar nodes to return (1 to 100) |
| target | string | none | Optional second node; its score and rank are returned |
| seed | integer | 0 | Random seed; the same seed gives the same result |
| dimensions | integer | 32 | Embedding length (2 to 128) |
| walk_length | integer | 20 | Nodes per random walk (2 to 80) |
| walks_per_node | integer | 10 | Walks started from each node (1 to 40) |
| window | integer | 5 | Context window on a walk (1 to 10) |
| epochs | integer | 2 | Training passes (1 to 10) |

## Output
`result` is an object:
- `node`: the query node `{id, label}`
- `similar`: up to `top_k` nodes `{id, label, score, is_neighbor}`, score (cosine, -1 to 1, 6 decimals) high to low, ties by node id; `is_neighbor` says whether there is a direct edge
- `compared_with`: how many nodes were ranked (every other node with at least one edge)
- `settings`: the settings used, the seed, the number of walks, and how edge direction was treated
- `target` (only if `target` was given): `{id, label, score, rank, is_neighbor}`

Example (`graph_id="karate", node="m1", top_k=5`): m12 (0.871), m5, m17, m22, m6, all from the instructor's own faction. `result_graph_id` is always null. If `top_k` nodes would pass 8 KB (long labels on `airports`), fewer are listed and the summary says how many.

## Graphs it supports
Undirected and directed graphs (walks ignore edge direction, since DeepWalk is defined on undirected graphs); weights are ignored. Results are approximate: different seeds give slightly different scores, but the same seed always gives the same output.

## Errors
- Unknown `graph_id`: use `list_graphs`.
- `node` missing or not in the graph, or `target` not in the graph: use `lookup_node`.
- `node` or `target` has no edges: random walks never visit it, so it has no embedding.
- The query node is the only node with edges, so there is nothing to compare.
- `top_k`, `seed` or a setting outside its range, or an unknown parameter.
- Settings too heavy to finish quickly: lower the walk or training settings.