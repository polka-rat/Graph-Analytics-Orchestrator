# maximal_cliques

**Author:** a20d8c29 · **Tier:** hard · **Category:** community

## What it computes
Every **maximal clique** in the graph, ranked largest first. A *clique* is a set of nodes in
which every pair is directly connected; it is *maximal* when no further node can be added
without breaking that property. Note this is not the same as the *maximum* clique: a graph
has many maximal cliques, and the largest of them is the maximum one.

The algorithm is **Bron–Kerbosch with pivoting**. It explores three sets:

- `R` — the clique built so far,
- `P` — candidates that could still extend it,
- `X` — nodes already explored, which stops a clique being reported twice.

When `P` and `X` are both empty, `R` cannot be extended and is therefore maximal.

Pivoting is what makes it tractable. A pivot `u` is chosen from `P ∪ X` maximising
`|P ∩ N(u)|`, and the search branches only over `P \ N(u)`. The justification: any maximal
clique either excludes `u` or contains one of `u`'s non-neighbours, so the skipped branches
cannot yield a clique that is not found elsewhere. Without pivoting the search blows up on
a graph as dense as `airports`.

Worst-case complexity is **O(3^(n/3))**, the Moon–Moser bound on the number of maximal
cliques, but the practical cost is proportional to the number actually present.
Neighbourhoods are stored as Python `set`s so intersection is cheap, and the recursion is
run on an explicit stack rather than the call stack.

Measured on `airports` (500 nodes, 20,058 edges): **17,575 maximal cliques, largest 24
members, 0.46 s** — comfortably inside the 30 s limit. The enumeration is identical to
`networkx.find_cliques` on all five datasets.

## When to use it
Questions about tightly knit groups where everyone is connected to everyone:

- "What is the largest group of airports that all fly to each other?"
- "Which characters in Les Misérables all appear together in the same chapters?"

For looser groupings that need not be complete, use `louvain`, `label_propagation` or
`k_core` instead.

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| top_k | integer | 10 | How many of the largest cliques to return (1 to 100) |
| min_size | integer | 1 | Ignore cliques smaller than this; use 3+ to skip plain pairs |

The default `min_size` of 1 matches `networkx.find_cliques`, which reports an isolated node
as a clique of one. `projects` contains such a node.

## Output
`result` is a list of cliques, largest first. Each entry carries the clique's registered
subgraph id, its size, and its members as node references.

```json
[{"graph_id": "karate~1", "size": 5,
  "nodes": [{"id": "m1", "label": "Member 1 (instructor)"}, {"id": "m2", "label": "Member 2"}]}]
```

This is a **↪ subgraph-returning tool**: every returned clique is registered with the store
via `store.subgraph(...)`, so another tool can be run on it next, and `result_graph_id` is
the largest clique's id.

Ranking is by size descending, then by the sorted list of node ids ascending, so the output
is deterministic. `top_k` is an upper bound: cliques of 24 airports with long labels would
overflow the 8 KB response limit, so the lowest-ranked entries are dropped until the
response fits, and the summary says how many of how many are shown. In the extreme case of
a single clique too large to list in full, its member list is itself truncated and the
summary says so.

## Graphs it supports
All of them. A clique is an undirected notion, so on a directed graph such as `airports`
direction is ignored: `u` and `v` count as adjacent if an edge runs either way between
them. Edge weights are not used. Self-loops are ignored, since a node is not its own
neighbour. Subgraphs registered by other tools work as input too.

## Errors
| Error | Cause |
| --- | --- |
| `No graph with id '...'. Use list_graphs ...` | Unknown `graph_id` |
| `Graph '...' has no nodes, so it contains no cliques.` | Empty graph |
| `top_k must be a whole number from 1 to 100; got ...` | `top_k` out of range or not an integer |
| `min_size must be a whole number of 1 or more; got ...` | Bad `min_size` |
| `Graph '...' has no maximal clique with at least N nodes; the largest one has M.` | `min_size` above the maximum clique size |
| `Unknown parameter(s): ...` | A parameter not in the manifest |

## Tests
Nine tests in `tests/test_maximal_cliques.py`: the complete enumeration is compared with
`networkx.find_cliques` on all five datasets; the top result is a genuine maximum-size
clique; every pair inside every returned clique is verified adjacent on `lesmis` and
`airports`; results are ordered largest first and each is registered as a retrievable
subgraph with `result_graph_id` pointing at the largest; `min_size` filters the size-1
clique in `projects`; an impossible `min_size` gives a helpful error; `top_k` and the 8 KB
bound hold on `airports`; five invalid inputs each return an error rather than crashing;
and two runs agree on clique membership, order and summary.
