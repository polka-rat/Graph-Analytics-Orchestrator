# node_embedding_similarity

**Author:** 7780ae37 | **Tier:** hard | **Category:** structure

Finds the nodes most similar to a query node using DeepWalk-style random-walk embeddings and cosine similarity. "Similar" means: appears in similar neighbourhoods and plays a similar structural role.

## Parameters
| name | type | default | description |
| --- | --- | --- | --- |
| `graph_id` | string | required | graph to analyse |
| `node` | string | required | query node id |
| `top_k` | integer | 10 (max 100) | nodes to return |
| `seed` | integer | 0 | random seed; same seed -> same output |
| `dimensions` | integer | 32 (1-128) | embedding size |
| `walk_length` | integer | 40 (2-100) | nodes per random walk |
| `num_walks` | integer | 40 (1-100) | walks started from every node |
| `window` | integer | 5 (1-10) | co-occurrence window |

## Algorithm
1. **Random walks.** `num_walks` uniform walks of `walk_length` nodes from every connected node, using `random.Random(seed)` (neighbour lists are sorted first, so the result depends only on the seed). Edge direction and weights are ignored, so walks never dead-end.
2. **Skip-gram co-occurrences.** For every pair of nodes at most `window` steps apart in a walk, count one co-occurrence (both directions). Counting is vectorised with NumPy `bincount`.
3. **PPMI.** `max(0, log(C_ij * total / (row_i * row_j)))`.
4. **Truncated SVD.** Embedding = `U[:, :d] * sqrt(S[:d])`, rows normalised to unit length. Levy & Goldberg (2014) showed skip-gram with negative sampling implicitly factorises a shifted PMI matrix, so this is a deterministic, fast alternative to training word2vec (no randomness in the optimiser, no sign/ordering instability).
5. **Rank** all other connected nodes by cosine similarity to the query; scores rounded to 6 decimals, ties broken by node id.

Cost: O(num_walks * n * walk_length) for walks plus an O(n^3) dense SVD; about a second on `airports` (500 nodes). Graphs over 3000 nodes return an error asking for a subgraph.

## Output
`result` is a list of `{"id", "label", "score"}` (score = cosine similarity in [-1, 1]), the query node excluded. An isolated query node returns an empty list with an explanation.

## Edge cases
Unknown graph or node, bad `top_k`/`seed`/numeric parameters, unknown parameters, a graph with fewer than 2 nodes and graphs with more than 3000 nodes return `status: "error"` with a fix. Never crashes; deterministic; no network, files or printing.

## Notes
Different seeds give slightly different scores because the walks differ, but the top results are stable (see tests).
