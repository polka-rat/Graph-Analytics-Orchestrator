# link_prediction

**Author:** 92711a92 · **Tier:** medium · **Category:** structure

## What it computes
Scores every pair of nodes that is **not** already linked by how likely a link between them is, then returns the top_k pairs. The scores follow NetworkX's definitions, where N(x) is the neighbour set and deg(x) = |N(x)|:

| method | score of pair (u, v) |
| --- | --- |
| `adamic_adar` (default) | Σ over common neighbours w of 1 / log deg(w) |
| `resource_allocation` | Σ over common neighbours w of 1 / deg(w) |
| `jaccard` | \|N(u) ∩ N(v)\| / \|N(u) ∪ N(v)\| |
| `common_neighbors` | \|N(u) ∩ N(v)\| |
| `preferential_attachment` | deg(u) · deg(v) |

Instead of testing all V² pairs, it walks over each node w and every pair of w's neighbours. Each pair visited has w as a common neighbour, so the common-neighbour counts and sums build up in O(Σ deg(w)²) time. Pairs with no common neighbour score 0, except under preferential attachment, so they are only enumerated when that method is used or when there aren't enough positive pairs to fill top_k. Ties are broken by node ids in ascending order, and every pair is reported with the smaller id first.

## When to use it
- "Who should the karate club's instructor connect with next?" (`node="m1"`)
- "Which new non-stop route is most likely to appear?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| node | string | none | Only predict links for this node |
| method | string | adamic_adar | One of the five methods above |
| top_k | integer | 10 | How many pairs to return (1 to 100) |

## Output
```json
[{"source": {"id": "m3", "label": "Member 3"}, "target": {"id": "m34", "label": "Member 34 (administrator)"},
  "score": 4.719381, "common_neighbors": 6}, ...]
```
`summary` names the top pair. If top_k would make the output bigger than 8 KB, the list is shortened and the summary says so. Does not return `result_graph_id`.

## Graphs it supports
Undirected graphs. On a directed graph it uses the undirected version, where a pair counts as linked if an edge exists in either direction, and says so in the summary. Weights are ignored.

## Errors
- Unknown `graph_id`, `node` or `method`, or an unknown extra parameter.
- `top_k` not a whole number from 1 to 100.
- No unlinked pairs (for example a complete graph), so there is nothing to predict.
