# personalized_pagerank

**Author:** 81c01533 · **Tier:** medium · **Category:** centrality

## What it computes
Personalized PageRank (Random Walk with Restart) from a single seed node. A walker starts at the seed; at each step it follows an outgoing edge with probability `alpha` (chosen proportionally to edge weight), or restarts at the seed with probability `1 - alpha`. The score of a node is the stationary probability of the walker being there, so nodes close to or strongly connected to the seed score highest. Dangling nodes (no outgoing edges) send their mass back to the seed. Scores are computed by power iteration until the L1 change drops below `tol` or `max_iter` is reached. Each iteration costs O(V + E), so the total is O(max_iter · (V + E)).

## When to use it
Questions about relevance or similarity relative to one specific node: local community detection, recommendations, "nearest" nodes in a network.
- "Which characters are most closely related to node `m1` in the karate club graph?"
- "What courses are most relevant to this course in the prerequisite graph?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| seed_node | string | (required) | Node id the walk restarts at; scores are relative to this node |
| top_k | integer | 10 | How many results to return (1 to 100) |
| alpha | number | 0.85 | Probability of continuing the walk, in [0, 1). `0` keeps all mass on the seed |
| max_iter | integer | 100 | Maximum number of power iterations (1 to 1000, capped to stay within the time limit) |
| tol | number | 1e-5 | Convergence threshold on the L1 change between iterations (positive and finite) |

## Output
`result` contains `top_items`: the top-`k` nodes in descending score order, each as a `node_ref` (`id`, `label`) plus `score`, rounded to 4 decimal places. The seed itself is included in the ranking and usually ranks first. The tool does not return a `result_graph_id`.

```json
{
  "top_items": [
    {"id": "m1", "label": "Mr. Hi", "score": 0.3021},
    {"id": "m34", "label": "John A", "score": 0.0412}
  ]
}
```

`summary` is a one-line text version naming only the first 3 nodes (to keep the output under 8 KB even at `top_k=100`), e.g. `Top 3 nodes most relevant to Mr. Hi (m1) : ...`. Output is deterministic: same input gives the same output.

## Graphs it supports
- Directed and undirected graphs (undirected edges are walked in both directions).
- Weighted and unweighted graphs (unweighted edges count as equal weight). Edge weights must be non-negative; graphs with negative weights return an error.
- Nodes unreachable from the seed get a score of 0.

## Errors
The tool returns an error (never raises) when:
- `graph_id` does not exist.
- An unknown parameter is passed.
- `seed_node` is missing, or is not a node in the graph.
- The graph has a negative edge weight.
- `top_k` is not an integer in 1 to 100.
- `alpha` is not a number in [0, 1) (booleans are rejected).
- `max_iter` is not an integer from 1 to 1000.
- `tol` is not a positive finite number (NaN and infinity are rejected).
