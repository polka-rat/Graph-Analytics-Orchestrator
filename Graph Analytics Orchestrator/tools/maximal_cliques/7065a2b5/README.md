# maximal_cliques

**Author:** 7065a2b5 · **Tier:** hard · **Category:** community

## What it computes
A clique is a set of nodes that are all directly connected to each other. A clique is *maximal* if no other node can be added to it. The tool lists every maximal clique using the Bron–Kerbosch algorithm with Tomita pivoting. Then it returns the largest cliques, biggest first, together with summary counts.

Bron–Kerbosch grows a clique `R` using candidate nodes `P` and skips nodes in `X`, which have already been tried. At each step it picks a pivot `u` from `P ∪ X`: the node with the most neighbours in `P`. Only candidates that are *not* neighbours of `u` start a new branch, because any clique containing a neighbour of `u` is also found through another branch. In the worst case the running time is O(3^(n/3)), which is the most maximal cliques a graph can have. On real graphs it is fast: all 17,575 maximal cliques of `airports` take about 0.1 s.

The search uses an explicit stack instead of recursion, so even a clique of thousands of nodes cannot exceed Python's recursion limit. Only the best `top_k` cliques are kept in memory. If a graph has more than 1,000,000 maximal cliques, the tool stops after about 2 s and returns an error that suggests a smaller subgraph or the `node` parameter. It does not run for minutes.

## When to use it
Use it for questions about groups in which everyone knows everyone, and about how large the most tightly connected group is.
- "What is the largest group of characters in *Les Misérables* who all appear with each other?"
- "Which tight friendship groups does the karate club instructor belong to?" (with `node`)

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| top_k | integer | 10 | How many of the largest cliques to return (1 to 100) |
| node | string | (none) | Only consider cliques that contain this node id |

The tool accepts some inputs that LLMs often send, rather than returning an error:
- `null` means the parameter's default, and `""` for `node` means no node.
- `top_k` may be `5.0` or `"5"`.
- `node` may be a number, such as `5` for node `"5"`. Letter case and extra spaces are ignored when exactly one node matches, so `"maa"` finds `MAA`.

## Output
`result` is a list of the `top_k` largest maximal cliques. Each entry has:
- `rank`
- `size`
- `graph_id`: the clique registered as a subgraph
- `members`: a list of `{"id", "label"}`

Cliques are ordered by size from largest to smallest. Cliques of the same size are ordered by their sorted lists of node ids. Members within a clique are sorted by node id. With `node`, only cliques that contain that node are listed.

`result_graph_id` is the subgraph of the largest clique, so another tool can run on it next.

The summary gives the size of the largest clique and its first few members. It also gives the total number of maximal cliques and how many have the largest size. It also notes these special cases:
- On directed graphs, that edge direction was ignored.
- On triangle-free graphs, that the graph has no triangles.
- On graphs without edges, that every node is a clique on its own.

The whole response is kept under 8 KB, in three steps:
1. The last cliques lose their `members` list first; their `size` and `graph_id` are still returned.
2. If that is not enough, the last entries are dropped.
3. If a single clique is still too big to list (more than about 150 members), its member list is shortened. The full clique stays available through its `graph_id`.

The summary says when any of these happens. On `airports`, where the largest clique has 24 airports, `top_k=10` lists the members of the first four cliques, and `top_k=100` lists only the first clique's members.

```json
[{"rank": 1, "size": 5, "graph_id": "karate~1",
  "members": [{"id": "m1", "label": "Member 1 (instructor)"}, {"id": "m14", "label": "Member 14"},
              {"id": "m2", "label": "Member 2"}, {"id": "m3", "label": "Member 3"}, {"id": "m4", "label": "Member 4"}]},
 {"rank": 2, "size": 5, "graph_id": "karate~2", "members": [...]}, ...]
```
Summary: *The largest clique in 'karate' has 5 nodes: Member 1 (instructor), Member 14, Member 2, Member 3 and Member 4 (subgraph 'karate~1'). 'karate' has 36 maximal cliques, 2 of the largest size.*

## Graphs it supports
- **Undirected graphs:** supported directly.
- **Directed graphs:** edge direction is ignored, so two nodes count as adjacent if an edge runs in either direction. This is the same as NetworkX's `find_cliques(G.to_undirected())`. The summary says so.
- **Weights** are ignored. Self-loops are ignored.
- **Triangle-free graphs** (bipartite graphs such as `projects`, or `courses`): every maximal clique is a single edge. The summary says the graph has no triangles.
- **Graphs without edges:** every node is its own maximal clique of size 1.
- **Subgraphs from other tools** (`filter_nodes`, other cliques, edge subgraphs): supported like any other graph.

## Errors
- `graph_id` is missing or unknown. The message suggests `list_graphs`.
- `node` is not in the graph. The message suggests `lookup_node`.
- `top_k` is not a whole number from 1 to 100.
- A parameter is unknown.
- The graph has no nodes.
- The graph has more than 1,000,000 maximal cliques. The message suggests a smaller subgraph or `node`.
