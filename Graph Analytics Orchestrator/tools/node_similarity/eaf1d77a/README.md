# node_similarity (easy)

Common neighbours and Jaccard similarity of nodes.

## What it computes
For nodes *a* and *b* with neighbour sets N(a), N(b):

- **common neighbours**: |N(a) ∩ N(b)|, not counting a and b themselves (as `nx.common_neighbors`)
- **Jaccard similarity**: |N(a) ∩ N(b)| / |N(a) ∪ N(b)|, or 0 if both have no neighbours (as `nx.jaccard_coefficient`)

## Modes
| Call | Answers |
| --- | --- |
| `node_a` + `node_b` | "How similar are Alice's and Bob's connections?" Returns both nodes, their degrees, the common-neighbour count, the Jaccard score and up to `top_k` shared neighbours. |
| `node_a` only | "Who is most similar to Alice?" Returns the `top_k` nodes with the highest non-zero Jaccard score. |

On directed graphs, `direction` chooses the neighbourhood: `out` (successors), `in` (predecessors) or `any` (default, both).

## Algorithm
Pair mode is a set intersection and union, O(d(a) + d(b)). Ranking mode only scores nodes that share a neighbour with `a`: it walks a → w → b and counts how often each b is reached. That count is |N(a) ∩ N(b)|, and the Jaccard score follows as cn / (d(a) + d(b) − cn). The cost is O(Σ_{w∈N(a)} d(w)), not O(n).

## Output and determinism
Scores are rounded to 6 decimals. Ranking is by Jaccard score (descending), then node id (ascending). Responses are trimmed to stay under 8 KB.

## Errors
Unknown graph, missing or unknown node, the same node twice, a bad `direction` or a bad `top_k` each return `status: "error"` with a hint (for example, use `lookup_node`).

## Example
```
python run_tool.py registry/tools/node_similarity/STUDENT_ID graph_id=airports node_a=MAA node_b=DEL
python run_tool.py registry/tools/node_similarity/STUDENT_ID graph_id=karate node_a=m1 top_k=5
```
