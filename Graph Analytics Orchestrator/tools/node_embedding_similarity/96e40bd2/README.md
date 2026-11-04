# node_embedding_similarity

**Author:** 96e40bd2 · **Tier:** hard · **Category:** structure

## What it computes
DeepWalk-style node embeddings, then the nodes whose embeddings are closest (cosine similarity) to a query node.
1. **Random walks:** `num_walks` walks of `walk_length` nodes from every node; each step moves to a uniformly random out-neighbour (a walk ends at a node with no out-edges).
2. **Context counts:** every pair of nodes at most `window` steps apart on a walk is counted as (node, context).
3. **Embedding:** DeepWalk's skip-gram with negative sampling implicitly factorises the shifted pointwise mutual information (PMI) matrix of these counts. The tool builds the positive PMI matrix and takes its truncated SVD (`U * sqrt(S)`, `dimensions` columns), using NumPy only.
4. **Similarity:** cosine similarity between the query vector and all other vectors.

Time is O(n * num_walks * walk_length) for the walks plus O(n^3) for the dense SVD; for the largest dataset (500 nodes) it takes well under a second. Memory is O(n^2), so graphs above 3000 nodes are refused.

## When to use it
- "Which airports play a similar role to Chennai?"
- "Which club members are positioned like the instructor?"

Similar means a similar position and neighbourhood in the graph, not shared attributes and not necessarily directly connected.

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| node | string | (required) | Node ID of the query node |
| top_k | integer | 10 | How many similar nodes to return (1 to 100) |
| walk_length | integer | 20 | Nodes per random walk (2 to 100) |
| num_walks | integer | 10 | Walks started from each node (1 to 100) |
| window | integer | 5 | Context window along a walk (1 to 10) |
| dimensions | integer | 32 | Embedding size (2 to 128) |
| seed | integer | 0 | Random seed; same seed gives the same output |

## Output
`result` is a list of `{"id", "label", "score"}` sorted by cosine score descending (ties by node id ascending, scores rounded to 6 decimals), excluding the query node. `result_graph_id` is `null`. The list may be shortened to keep the reply under 8 KB.
```json
{"status": "ok",
 "result": [{"id": "HYD", "label": "Rajiv Gandhi International Airport", "score": 0.961025}],
 "summary": "The node most similar to Chennai International Airport (MAA) in 'airports' is ...",
 "result_graph_id": null, "error": null}
```

## Graphs it supports
Directed (walks follow edge direction) and undirected graphs, weighted or not. Edge weights are ignored. Graphs with 3 to 3000 nodes.

## Errors
- Unknown graph (`list_graphs`), unknown or missing node (`lookup_node`).
- Node with no edges, or a node that never appears in any walk: explained, with a suggestion.
- Invalid `top_k` or integer parameter outside its range; unknown parameter.
- Graph with fewer than 3 nodes, more than 3000 nodes, or walk settings too large for the time limit.
