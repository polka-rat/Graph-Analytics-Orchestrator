# k_hop_neighborhood

**Author:** 32016695 ([ANONYMOUS]) · **Tier:** easy · **Category:** subgraph · Returns a subgraph (↪)

## What it computes
All nodes within `k` hops of a start node, found by breadth-first search (BFS) from that node. BFS visits nodes in rings: first the direct neighbours (1 hop), then their unseen neighbours (2 hops), and so on, stopping at `k`. Each node is recorded with the hop count at which it was first reached, which is its shortest hop distance. Time complexity is O(V + E) in the worst case, and usually far less because the search stops at `k` hops.

## When to use it
Questions about who or what is "near" a node, counted in steps rather than distance:
- "Who is within two hops of Mr. Hi in the karate club?"
- "Which airports can I reach from Chennai with at most one change?" (`k=2`, `direction="out"`)
- "Which courses lead, directly or indirectly, to Operating Systems?" (`direction="in"`)

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| node | string | (required) | Id of the start node (use `lookup_node` to find it from a name) |
| k | integer | 2 | Maximum number of hops, 1 to 10 |
| direction | string | `"out"` | Directed graphs only: `out` follows edges forwards, `in` backwards, `both` ignores direction. Ignored on undirected graphs. |
| top_k | integer | 10 | How many found nodes to list, nearest first (1 to 100) |

## Output
`result` describes the neighbourhood:
```json
{
  "source": {"id": "m1", "label": "Member 1 (instructor)"},
  "k": 2, "direction": "both", "count": 25,
  "count_by_hops": {"1": 16, "2": 9},
  "nodes": [{"id": "m11", "label": "Member 11", "hops": 1}, ...],
  "truncated": true
}
```
- `count` and `count_by_hops` always cover every node found, even when `nodes` is cut short.
- `nodes` lists the nearest `top_k` nodes, sorted by hops and then by node id. The start node is not in it.
- `truncated` is true when `nodes` doesn't list everything. If long labels would push the response over 8 KB, the farthest nodes are dropped until it fits.
- `result_graph_id` is the id of a registered subgraph containing the start node and every node found (all of them, not just the listed ones) with the edges among them, so other tools can run on it. It is set whenever `status` is `ok`, even when nothing was found (then the subgraph is just the start node).

## Graphs it supports
Directed and undirected graphs, weighted or unweighted. Edge weights are ignored: only the number of hops counts. For a distance-based neighbourhood, use `shortest_path_weighted` instead.

## Errors
- Unknown `graph_id`: use `list_graphs`.
- Unknown `node`: use `lookup_node` to find the id.
- `k` not a whole number from 1 to 10.
- `direction` not one of `out`, `in`, `both`.
- `top_k` not a whole number from 1 to 100.
- Any parameter not listed above.

A node with no edges in the chosen direction is **not** an error: the result is `ok` with `count` 0 and a summary saying the node has no such edges.

## Input handling
LLMs don't always send clean values, so the tool accepts the unambiguous ones instead of failing:
- `k` and `top_k` may arrive as `2.0` or `"2"`; they are read as whole numbers. `2.5` or `"two"` is still an error.
- A node id in the wrong case (`maa` for `MAA`) or with spaces around it is accepted when it matches exactly one node.
- `direction` is case-insensitive.
- A missing `node` gives an error that says the parameter is missing, not "node None not found".
- The tool also works on graphs registered by other tools (ids like `airports~3`), and its own output can be fed back into it.

## Tests
`tests/test_k_hop_neighborhood.py` checks the results against NetworkX's `single_source_shortest_path_length` on every karate node for k = 1, 2, 3, and on airports for all three directions. It also checks the registered subgraph, the sort order and `top_k`, the 8 KB limit, the empty result, every error case, and that results are deterministic.
