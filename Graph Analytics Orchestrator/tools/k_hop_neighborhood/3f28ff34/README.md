# k_hop_neighborhood

**Author:** 3f28ff34 · **Tier:** Easy · **Category:** Subgraph

## What it computes
Finds every node that can be reached from a start node in at most `k` steps (hops).
It uses breadth-first search (BFS): first the direct neighbours (1 hop), then their
neighbours (2 hops), and so on, up to `k`. Each node found is reported with its hop
distance. Time complexity: O(V + E).

## When to use it
For questions about who or what is "near" a node:
- "Who is within two hops of Member 1 in the karate club?"
- "Which airports can I reach from Chennai with at most one stop?" (1 stop = 2 hops)

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| node | string | (required) | Id of the start node, e.g. `MAA` or `m1`. Use `lookup_node` to find the id from a name |
| k | integer | 1 | Number of hops; must be 1 or more (no upper limit) |
| top_k | integer | 10 | How many of the nearest nodes to list (1 to 100) |

## Output
- `source`: the start node.
- `k`: the number of hops used.
- `count`: total number of nodes found (the start node is not counted).
- `nodes`: the nearest `top_k` nodes, each with `id`, `label` and `distance`.
  Sorted by distance, then by id.
- `result_graph_id`: a new subgraph with the start node and **all** nodes found
  (not only the listed ones). Other tools can run on it next.

Example: `graph_id=karate node=m1 k=2 top_k=2`
```json
{"status": "ok",
 "result": {"source": {"id": "m1", "label": "Member 1 (instructor)"}, "k": 2, "count": 25,
            "nodes": [{"id": "m11", "label": "Member 11", "distance": 1},
                      {"id": "m12", "label": "Member 12", "distance": 1}]},
 "summary": "25 nodes are within 2 hop(s) of Member 1 (instructor) (m1); the nearest 2 are listed with their distances, and the full set is in result_graph_id.",
 "result_graph_id": "karate~1", "error": null}
```
Node ids are compared as text, so `m11` comes before `m2`.

## Graphs it supports
- Undirected and directed graphs. On directed graphs only **outgoing** edges are followed
  (same as NetworkX `ego_graph`).
- Weighted and unweighted graphs. Weights are ignored: every edge counts as one hop.
- If the node has no outgoing edges, the result is `ok` with `count` 0 (not an error).

## Errors
| When | Message says |
| --- | --- |
| Unknown graph | No graph with that id; use `list_graphs` |
| Node missing or not in the graph | Node not found; use `lookup_node` |
| `k` is not a whole number of at least 1 (e.g. `0`, `2.5`, `"2"`, `true`) | k must be a whole number of at least 1 |
| `top_k` outside 1 to 100 | top_k must be a whole number from 1 to 100 |
| Unknown parameter | Lists the unknown parameter |

If the list would make the output larger than 8 KB, the farthest nodes are dropped from
the list (the summary says how many are listed). `count` and the subgraph stay complete.
