# link_prediction (hard)

Top-k likely missing edges, scored by neighbourhood similarity.

## Methods (definitions match NetworkX)
| method | score of a non-adjacent pair (u, v) |
| --- | --- |
| `adamic_adar` (default) | Σ over common neighbours w of 1 / log d(w) |
| `resource_allocation` | Σ over common neighbours w of 1 / d(w) |
| `jaccard` | \|N(u) ∩ N(v)\| / \|N(u) ∪ N(v)\| |
| `common_neighbors` | \|N(u) ∩ N(v)\| |
| `preferential_attachment` | d(u) · d(v) |

Only pairs that are **not** connected are candidates. Pairs scoring 0 are omitted. Directed graphs are scored on their undirected view: a pair linked in either direction counts as connected. Self-loops are ignored.

## Modes
- **Global** (no `node`): the `top_k` best pairs in the whole graph. Each pair is written with `source` < `target` by id.
- **Single node** (`node` given): "Who should Alice connect with next?" Returns the `top_k` best partners for that node.

## Algorithm
1. Build undirected neighbour sets and sort nodes by id.
2. For the common-neighbour based scores, visit each node u in id order and walk u → w → v, keeping only v after u that is not already a neighbour of u. Each step adds the weight of w to v's score. Only pairs at distance 2 can score above 0, so this costs O(Σ d(w)²) instead of O(n²).
3. For preferential attachment, every non-adjacent pair has a positive score (unless a node is isolated). Each row d(u) · d(v>u) is computed with NumPy, and existing edges are zeroed out.
4. **Bounded top-k:** pairs are produced in ascending (u, v) order. A tie with the current k-th best always loses the id tie-break, so a new pair enters only if it scores *strictly* higher. The best list never grows beyond k.

## Output and determinism
Each result has `source` and `target` (id and label), `score` (rounded to 6 decimals) and `common_neighbors`. The order is score descending, then source id, then target id. Responses are trimmed to stay under 8 KB.

## Errors
Unknown graph, unknown method, unknown node, a bad `top_k` or a graph with fewer than two nodes each return `status: "error"`.

## Example
```
python run_tool.py registry/tools/link_prediction/STUDENT_ID graph_id=karate
python run_tool.py registry/tools/link_prediction/STUDENT_ID graph_id=karate node=m1 method=jaccard top_k=5
```
