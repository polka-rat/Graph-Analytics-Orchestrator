# bipartite_check

**Author:** 7780ae37 | **Tier:** medium | **Category:** structure | returns a subgraph

Decides whether a graph is bipartite (two groups, no edge inside a group). Gives the two sides if it is, an odd cycle as proof if it is not.

## Parameters
| name | type | description |
| --- | --- | --- |
| `graph_id` | string | graph to check |
| `top_k` | integer (default 10, max 100) | nodes to list per side |

## Algorithm
BFS 2-colouring. For each unvisited node (in sorted id order) start a new component with colour 0, and give every newly found neighbour the opposite colour. If an edge joins two nodes of the same colour, the graph is not bipartite. The odd cycle is built from the two BFS-tree paths of that edge up to their lowest common ancestor (+ the closing edge), so its length is odd. Edge direction is ignored (same as NetworkX's `bipartite.color`). A self-loop is an odd cycle of length 1. Time O(V + E), memory O(V).

For a disconnected graph the colour of each component is only fixed up to swapping; this tool puts the smallest-id node of every component on `side_a`.

## Output
- bipartite: `result = {"is_bipartite": true, "components": c, "sides": [{"side": "side_a", "size", "graph_id", "nodes": [...]}, {"side": "side_b", ...}]}`; `result_graph_id` is the larger side's subgraph (ties: side_a).
- not bipartite: `result = {"is_bipartite": false, "odd_cycle_length", "odd_cycle": [nodes], "graph_id"}`; `result_graph_id` is the cycle's induced subgraph. Cycles longer than 50 nodes are shortened in `odd_cycle` but `odd_cycle_length` is exact.

Each side's `graph_id` is the induced subgraph on that side, so it can be passed to other tools (note: it has no internal edges, by definition).

## Edge cases
Unknown graph, bad `top_k` and unknown parameters return errors; an empty graph returns an error; every node is returned with id and label.
