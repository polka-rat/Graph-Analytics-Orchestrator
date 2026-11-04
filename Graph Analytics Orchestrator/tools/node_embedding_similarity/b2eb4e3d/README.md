# node_embedding_similarity

**Author:** b2eb4e3d · **Tier:** hard · **Category:** structure

## What it computes
Builds a deterministic spectral embedding and ranks nodes by cosine similarity. With the symmetric adjacency matrix A and degree matrix D, it takes the eigendecomposition of S = D^-1/2 A D^-1/2 (numpy.linalg.eigh) and keeps the `dimensions` eigenpairs with the largest absolute eigenvalue. Node i is embedded as the i-th row of Q_k times Lambda_k^t, where t is `walk_length`, so inner products approximate S^(2t), a random-walk overlap. A group of tied eigenvalues is never split, which makes cosine similarity independent of the basis chosen inside an eigenspace. Time is O(n^3) for n nodes, memory O(n^2); graphs above 1500 nodes are rejected. No random numbers are used.

## When to use it
Use it to find nodes with similar neighbourhoods, or the most alike pair of nodes. Example questions:
- "Which airports are structurally most similar to Chennai?"
- "Which two characters in Les Miserables play the most similar roles?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| node | string | none | Query node id. If omitted, the most similar pairs are returned |
| top_k | integer | 10 | How many results to return (1 to 100) |
| dimensions | integer | 16 | Embedding dimensions (1 to 128) |
| walk_length | integer | 2 | Eigenvalue power t (1 to 10) |
| use_weights | boolean | false | Use edge weights as connection strength (finite, non-negative) |
| seed | integer | 0 | Accepted and ignored: the method is deterministic |

## Output
With `node`: `result` is a list of up to `top_k` entries `{id, label, score}`, best first, ties broken by node id ascending. The query node itself is not listed. Without `node`: a list of `{node_a, node_b, score}` where each node is `{id, label}` and node_a's id is smaller, sorted by score descending then by (node_a id, node_b id). Scores are cosine similarities in [-1, 1], rounded to 6 decimals. The list is trimmed if needed to stay under 8 KB. `result_graph_id` is null.

## Graphs it supports
Directed and undirected graphs, weighted or unweighted. Directions are ignored (a pair joined both ways uses the smaller weight when weights are used). Self-loops are ignored. A node with no edges has a zero embedding and similarity 0 to all nodes. A graph with no edges gives all-zero scores.

## Errors
Every error is returned as `error(...)`, never raised:
- Unknown or non-string `graph_id`.
- `node` given but not in the graph (use `lookup_node`).
- `top_k`, `dimensions` or `walk_length` not a whole number in range (booleans, strings and floats are rejected).
- `use_weights` not a boolean, or `seed` not a whole number.
- The graph has no nodes, or more than 1500 nodes.
- `use_weights` is true and an edge weight is negative or not finite.
- The eigendecomposition fails or gives non-finite values.
- An unknown parameter is passed.