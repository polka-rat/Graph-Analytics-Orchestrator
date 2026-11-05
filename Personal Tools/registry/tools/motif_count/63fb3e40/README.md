# motif_count

**Author:** 63fb3e40 · **Tier:** hard · **Category:** structure

## What it computes
How often each small pattern (motif) of 3 or 4 nodes occurs in a graph, which nodes take part in a
pattern most often, and how each count compares with a random graph.

**Size 3 (default): the triad census.** Every set of three nodes is classified by the links among
them.
- **Directed graphs** have the 16 Holland–Leinhardt types, exactly as in NetworkX's
  `triadic_census`. Each code counts the Mutual, Asymmetric (one-way) and Null pairs, plus a letter
  for the shape: for example `030T` is the feed-forward loop A->B->C, A->C, `030C` the 3-cycle
  A->B->C->A, and `300` the fully mutual triangle.
- **Undirected graphs** have four types: empty, single edge, open triad (A-B-C with A and C
  unlinked) and triangle.

The tool uses the Batagelj–Mrvar algorithm. For each linked pair v < u it looks at the nodes linked
to v or u, and counts each connected triad exactly once, from its smallest node. Each triad's six
possible arcs form a 6-bit code, and a 64-entry table built at import time maps the code to its
type. Because every connected triad is visited, each of its three nodes can be credited with it,
which gives every node's counts. Triads with a single linked pair are counted by formula
(`n - 2 - |N(u) ∪ N(v)|` per pair), and the empty ones are `C(n, 3)` minus all the rest.
Time O(m · max_degree).

**Size 4: the six connected 4-node graphlets**, with direction ignored: `4_path`, `4_star`,
`4_cycle`, `tailed_triangle`, `diamond` and `4_clique`. This works in two steps.
1. For each node v, count the copies of every pattern through v, allowing extra links among the
   four nodes. Closed formulas, by v's position in the pattern, use degrees, triangles per edge,
   common-neighbour counts and the 4-cliques. For example, 4-cycles through v are
   Σ_w C(common neighbours of v and w, 2), and stars with v as the hub are C(d_v, 3).
2. Each denser pattern contains a fixed number of copies of every sparser one. For example, a
   4-clique holds 6 diamonds, 3 4-cycles, 12 tailed triangles, 4 stars and 12 paths. So the tool
   subtracts those, densest pattern first, leaving the exact number of 4-node sets that *induce*
   each pattern. Graph-wide counts are the per-node sums divided by 4.

Time O(m · max_degree²) at worst. On airports both sizes take under a second.

**Random baseline.** Each pattern's `expected_random` is its expected count in a random graph with
the same number of links:
- **Directed graphs:** each pair of nodes is independently mutual, one-way (either direction) or
  unlinked, with the observed proportions.
- **Undirected graphs and size 4:** the Erdős–Rényi graph of the same density.

`ratio_to_random` above 1 means the pattern is over-represented, which is the usual definition of
a network motif. Self-loops and edge weights are ignored.

## When to use it
Questions about the small building blocks of a network, or about how clustered it is:
- "Which small patterns are most common in the airport network?"
- "How many triangles (or feed-forward loops, 3-cycles, squares, 4-cliques) are there?"
- "Which characters of Les Misérables are in the most triangles?" (`motif="triangle"`)
- "How many triangles is the instructor part of?" (`node="m1"`)
- "Are triangles more common than in a random network?" (`ratio_to_random`)

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| size | integer | 3 | Nodes per pattern: 3 (triads) or 4 (4-node graphlets, direction ignored). If left out with a `motif`, it follows the motif |
| motif | string | none | Pattern to focus on: its count and the nodes in the most copies of it. Defaults to `triangle` for size 3 and `4_clique` for size 4 |
| node | string | none | Also return how many copies of each pattern this node is in, and its rank for the focus motif |
| top_k | integer | 10 | How many top nodes to list for the focus motif (1 to 100) |

**`motif` names.** Spaces, hyphens and case do not matter.
- **Any graph:** `triangle` and `open_triad`. On a directed graph these ignore direction:
  `triangle` covers the 7 closed types and `open_triad` the 6 open ones.
- **Directed graphs:** any connected triad, by code or by name. `021D` out_star, `021U` in_star,
  `021C` chain, `111D` mutual_with_in, `111U` mutual_with_out, `030T` feed_forward_loop,
  `030C` cycle, `201` mutual_wedge, `120D` out_star_mutual, `120U` in_star_mutual,
  `120C` chain_mutual, `210` near_mutual_triangle, `300` mutual_triangle.
- **4-node patterns:** `4_path`, `4_star`, `4_cycle`, `tailed_triangle`, `diamond`, `4_clique`.
- **Aliases:** `ffl`, `3_cycle`, `wedge`, `square`, `paw`, `claw`, `k4`, `3_path` and a few more.

## Output
`result` is an object. It does not return a subgraph (`result_graph_id` is null). For karate:

```json
{"graph_id": "karate", "directed": false, "size": 3, "number_of_nodes": 34, "number_of_edges": 78,
 "census": {"empty": 3971, "single_edge": 1575, "open_triad": 393, "triangle": 45},
 "connected_subgraphs": 438,
 "motifs": [{"motif": "open_triad", "pattern": "A-B-C, A and C unlinked", "count": 393, "share": 0.89726,
             "expected_random": 298.786239, "ratio_to_random": 1.315322},
            {"motif": "triangle", "pattern": "A-B-C-A", "count": 45, "share": 0.10274,
             "expected_random": 16.083731, "ratio_to_random": 2.797858}],
 "triangles": 45, "open_triads": 393, "transitivity": 0.255682,
 "focus": {"motif": "triangle", "pattern": "A-B-C-A", "count": 45, "share": 0.10274,
           "expected_random": 16.083731, "ratio_to_random": 2.797858, "nodes_with_motif": 32,
           "top_nodes": [{"id": "m1", "label": "Member 1 (instructor)", "count": 18},
                         {"id": "m34", "label": "Member 34 (administrator)", "count": 15}],
           "returned": 2, "truncated": true},
 "node": null}
```

**Fields for every call**
- `census`: every type and its count. For directed graphs the keys are the 16 codes, identical to
  `networkx.triadic_census`. For size 4 it holds the six connected graphlets.
- `connected_subgraphs`: how many node sets of this size are connected.
- `motifs`: the connected types, most common first. Each has its `count` and its `share` of the
  connected subgraphs, plus the random baseline. Directed rows also carry the triad `code`, for
  example `{"code": "030T", "motif": "feed_forward_loop", "pattern": "A->B->C, A->C", ...}`.

**Size 3 only**
- `triangles` and `open_triads`, with direction ignored.
- `transitivity`, equal to `3·triangles / (3·triangles + open_triads)`, as `networkx.transitivity`.
- For directed graphs, `dyads`: the mutual, asymmetric and null pairs.

**Size 4 only**
- `direction_ignored`: true for a directed graph.

**`focus`: the focus motif**
- Its count and random baseline.
- `top_nodes`: the nodes in the most copies, sorted by count and then by id. Only nodes with a
  non-zero count are listed.
- `nodes_with_motif`: how many nodes have one at all.
- `returned` and `truncated`.
- For a directed group, `includes`: the triad codes it covers.

**`node`:** null unless `node` is given. Then it holds the node's `counts` for every motif and its
`rank` (1 = most) for the focus motif.

**Size limit:** if `top_k` would push the response past 8 KB, `top_nodes` is shortened and the
summary says so.

## Graphs it supports
Directed and undirected, weighted or unweighted (weights are ignored), connected or not, and
registered subgraphs. Self-loops are skipped, since a pattern needs distinct nodes. Directed-only
motifs such as `feed_forward_loop` return an error on an undirected graph. Size 4 treats a directed
graph as undirected and says so. A graph with fewer nodes than `size` gets all-zero counts and a
summary that says why.

## Errors
- Unknown `graph_id`: use list_graphs to see the available graphs.
- The graph has no nodes (e.g. an empty registered subgraph).
- `size` other than 3 or 4, or a `size` that disagrees with the `motif`'s number of nodes.
- Unknown `motif`: the error lists the valid names for that graph.
- A directed pattern asked of an undirected graph.
- A disconnected type (`003`, `012`, `102`) as the motif: its count is in `census`.
- `node` not in the graph: use lookup_node to find ids.
- `top_k` not a whole number from 1 to 100.
- Unknown parameters.
