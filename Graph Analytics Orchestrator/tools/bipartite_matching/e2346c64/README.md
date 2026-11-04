# bipartite_matching (e2346c64)

Maximum-cardinality matching in an undirected bipartite graph using the **Hopcroft–Karp** algorithm.
A matching is a set of edges with no node in common; a maximum matching has as many edges as possible
(e.g. the most students that can each get a different project they are willing to do).

## Parameters
| name | type | default | meaning |
| --- | --- | --- | --- |
| `graph_id` | string | required | undirected bipartite graph, e.g. `projects` |
| `top_k` | integer | 100 (max 100) | how many matched pairs, and unmatched nodes per side, to list |

## Output
`result` holds `matching_size`, `left_side`/`right_side` (side names), `left_count`, `right_count`,
`max_possible` (= smaller side), `perfect`, `pairs` (each `{left_side: node, right_side: node}`, sorted
by the left node's id), `pairs_truncated`, `unmatched` nodes per side and `unmatched_counts`.

## How the sides are found
1. If every node has a `side` attribute with exactly two values and every edge joins different
   values, those are the sides (`projects`: project / student). The alphabetically first value is the left side.
2. Otherwise the graph is 2-coloured by BFS (sides `side_A` / `side_B`); an odd cycle means the graph is
   not bipartite, and the tool returns an error naming an edge on that cycle.

## Algorithm
Hopcroft–Karp: repeat (a) a BFS from all free left nodes that layers the graph by shortest
alternating-path distance, then (b) DFS from each free left node along the layers, flipping every
vertex-disjoint shortest augmenting path found. The DFS is iterative (no recursion limit).
Neighbours are visited in sorted order, so the result is deterministic. O(E·√V).
Edge weights are ignored (cardinality matching).

## Errors
Directed graph, non-bipartite graph, empty graph, unknown graph, bad `top_k` or unknown parameter
return `status: "error"` with a message on how to fix it.

## Tests
`python -m pytest registry/tools/bipartite_matching/e2346c64/tests`
