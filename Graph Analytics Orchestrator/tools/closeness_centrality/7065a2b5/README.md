# closeness_centrality

**Author:** 7065a2b5 · **Tier:** medium · **Category:** centrality

## What it computes
Closeness centrality measures how near a node is to every other node. For a node `u`, let `r` be the number of other nodes it reaches, `D` the sum of those shortest-path distances, and `n` the number of nodes in the graph. Then

    closeness(u) = (r / D) * (r / (n - 1))

The first factor is the inverse of the average distance. The second is the Wasserman–Faust correction: it scales the score down when `u` reaches only part of the graph, so nodes in small components don't look central. A node that reaches nothing scores 0. This is the same as NetworkX's `closeness_centrality` with its defaults (`wf_improved=True`).

Shortest paths come from one breadth-first search per node (hop counts) or one run of Dijkstra's algorithm per node (`weighted=true`). That costs O(n·(n+m)) for hop counts and O(n·m·log n) for weights. On `airports` (500 nodes, 20,058 edges) it takes about 0.2 s for hop counts and 0.7 s weighted.

## When to use it
Use it for questions about who is closest to everyone, or who can reach the rest of the network fastest.
- "Which airport can reach every other airport in the fewest flights?" (`graph_id=airports`, `direction=outgoing`)
- "How central is Valjean in *Les Misérables*?" (`node=c74`)

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| top_k | integer | 10 | How many of the most central nodes to return (1 to 100) |
| node | string | (none) | Return only this node's score and rank |
| weighted | boolean | false | Use edge weights as distances (Dijkstra) instead of hop counts |
| direction | string | `incoming` | Directed graphs only. `incoming` measures distance from the other nodes *to* each node (the NetworkX default). `outgoing` measures distance *from* each node to the others. |

The tool accepts some inputs that LLMs often send, rather than returning an error:
- `null` means the parameter's default, and `""` for `node` means no node.
- `top_k` may be `5.0` or `"5"`, and `weighted` may be `"true"` or `"false"`.
- `direction` ignores letter case and extra spaces, and accepts `in` and `out`.
- `node` may be a number, such as `5` for node `"5"`. Letter case and extra spaces are ignored when exactly one node matches, so `"maa"` finds `MAA`.

## Output
- **Without `node`:** `result` is a list of the `top_k` nodes, highest closeness first. Equal scores are ordered by node id.
  ```json
  [{"id": "m1", "label": "Member 1 (instructor)", "score": 0.568966},
   {"id": "m3", "label": "Member 3", "score": 0.559322}, ...]
  ```
  The summary gives the top node's average distance and how many nodes it reaches. It also says when the graph is disconnected or not strongly connected, and which direction was used.
- **With `node`:** `result` is one object with these fields:
  - `score`
  - `rank`, out of all nodes
  - `avg_distance`, to the nodes it reaches (`null` if it reaches none)
  - `reached`, the number of other nodes it reaches

  ```json
  {"id": "c74", "label": "Valjean", "score": 0.644068, "rank": 1, "avg_distance": 1.552632, "reached": 76}
  ```

Scores are rounded to 6 decimals. Weighted scores on `airports` are small, about 1/5500 per km, so they keep only about three significant digits.

The response stays under 8 KB. If `top_k` is close to 100 and the labels are long, the lowest-ranked entries are dropped and the summary says so. On `airports` with hop counts, 99 of 100 fit.

There is no `result_graph_id`; the tool returns no subgraph.

## Graphs it supports
- **Undirected and directed graphs.** On directed graphs, choose `direction`.
- **Weighted and unweighted graphs.** With `weighted=true` on an unweighted graph, every edge has weight 1, so the result is the same as hop counts. Negative or non-finite weights are rejected.
- **Zero-weight edges:** if a node's distances are all 0, its closeness is undefined. It is reported as 0, as in NetworkX, and the summary explains why.
- **Graphs without edges, or with a single node:** every score is 0, and the summary says no node can reach another.
- **Disconnected graphs** (e.g. `projects`), or directed graphs that aren't strongly connected (e.g. `courses`): the Wasserman–Faust correction applies and the summary says so.

## Errors
- `graph_id` is missing or unknown. The message suggests `list_graphs`.
- `node` is not in the graph. The message suggests `lookup_node`.
- `top_k` is not a whole number from 1 to 100.
- `weighted` is not `true` or `false`.
- `direction` is not `incoming` or `outgoing`.
- A parameter is unknown.
- The graph has no nodes.
- `weighted=true` on a graph with negative or non-finite edge weights.
