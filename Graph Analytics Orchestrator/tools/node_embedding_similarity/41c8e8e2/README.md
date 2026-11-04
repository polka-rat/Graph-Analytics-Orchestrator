# node_embedding_similarity

**Author:** 41c8e8e2 · **Tier:** hard · **Category:** structure

## What it computes
DeepWalk-style node embeddings and the nearest nodes to a query node.

1. Run `num_walks` uniform random walks of `walk_length` steps from every node (seeded NumPy generator).
2. Count how often two nodes appear within `window` steps of each other on a walk.
3. Convert the counts to a positive pointwise-mutual-information (PPMI) matrix and factorise it with a truncated SVD. This is the closed-form equivalent of DeepWalk's skip-gram with negative sampling (Levy & Goldberg, 2014), so it needs no training loop, is fast and is fully deterministic. Node vector = `U[:, :d] * sqrt(S[:d])`.
4. Rank every other node by cosine similarity to the query node.

Cost: walk generation O(n · num_walks · walk_length), co-occurrence O(n · num_walks · walk_length · window), SVD O(n³). About 0.2 s on the 500-node airports graph.

## When to use it
- "Which nodes play a similar role to Member 1?"
- "Which airports are most like Chennai?"

Similar nodes are those that live in similar neighbourhoods (they co-occur with the same nodes on random walks), not just nodes that are directly connected.

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| node | string | (required) | Query node id |
| top_k | integer | 10 | How many similar nodes to return (1 to 100) |
| dimensions | integer | 16 | Embedding size (1 to 128; capped at the number of nodes) |
| walk_length | integer | 40 | Steps per walk (2 to 200) |
| num_walks | integer | 10 | Walks per start node (1 to 50) |
| window | integer | 5 | Co-occurrence window (1 to 20) |
| seed | integer | 0 | Random seed |

## Output
`result` is a list of `{"id", "label", "score"}` where `score` is the cosine similarity (−1 to 1, rounded to 6 places), best first, query node excluded. Ties are broken by node id ascending. The list is shortened if it would exceed the 8 KB output limit (the summary says so). `result_graph_id` is `null`.

Same graph, parameters and seed always give the same output; a different seed changes the walks and so can change the ranking slightly.

## Graphs it supports
Directed or undirected, weighted or unweighted. Edge direction and weights are ignored: walks follow undirected neighbours uniformly. A node with no neighbours stays where it is, so it has a zero-ish embedding and similarity 0 to everything else. Graphs with fewer than 3 or more than 5,000 nodes are refused.

## Errors
Unknown graph; missing or unknown `node` (points to `lookup_node`); bad `top_k` or other numeric parameter (message gives the allowed range); unknown parameter name; graph too small or too large.
