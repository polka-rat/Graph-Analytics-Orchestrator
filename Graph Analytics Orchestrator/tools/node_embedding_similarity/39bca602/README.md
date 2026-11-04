# node_embedding_similarity

**Author:** 39bca602 · **Tier:** hard · **Category:** structure

## What it computes
Generates low-dimensional representations of network vertices using random walks (DeepWalk style) and matrix factorization (truncated SVD on shifted PPMI). Calculates cosine similarities to identify structurally similar nodes playing equivalent topological roles. Runs in $O(N \cdot \text{walk\_length} \cdot \text{num\_walks} + N^2 \cdot d)$.

## When to use it
- "Which airports play a structurally equivalent role to Chennai in global routes?"
- "Which karate club members occupy similar latent positions to Mr. Hi?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| `graph_id` | string | (required) | Graph identifier |
| `node` | string | (required) | Reference node ID |
| `dimensions` | integer | 16 | Latent embedding dimension |
| `walk_length` | integer | 10 | Steps per random walk |
| `num_walks` | integer | 5 | Walks initiated per node |
| `window_size` | integer | 2 | Context window radius |
| `seed` | integer | 0 | Random seed for determinism |
| `top_k` | integer | 10 | Number of top similar nodes to return (1 to 100) |

## Output
Returns a ranked list of top-$k$ most similar nodes with cosine similarity scores rounded to 6 decimal places. Does not register a subgraph (`result_graph_id` is null).

## Graphs it supports
Supports directed and undirected, weighted and unweighted graphs.

## Errors
- Unknown `graph_id`
- Node not found in graph
- Invalid `top_k`
- Unknown arguments