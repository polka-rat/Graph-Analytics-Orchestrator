# louvain

**Author:** b2d75536 · **Tier:** hard · **Category:** community

## What it computes
Communities, by greedily maximising modularity with the Louvain method. Modularity
compares the edge weight inside each community with the weight expected if the same
nodes kept their degrees but were wired at random:

    Q = sum_c [ L_c / m - resolution * (k_c / 2m)^2 ]

where `L_c` is the weight inside community `c`, `k_c` the total degree of its
members, and `m` the total edge weight. Above about 0.3 means clear community
structure.

The algorithm alternates two phases until nothing improves:

1. **Local moving.** Every node starts in its own community. Each node in turn is
   taken out of its community and put into whichever neighbouring community gives
   the largest modularity gain, `w(u,c) - resolution * tot_c * k_u / 2m`. Sweeps
   repeat until a sweep moves nobody.
2. **Aggregation.** Each community becomes a single node of a smaller weighted
   graph; the edges inside it become that node's self-loop, and edges between
   communities are summed. Phase 1 then runs on the smaller graph.

The levels are composed at the end to label each original node. Each sweep costs
O(E), and the graph shrinks quickly, so runs are near-linear in practice: the
500-node, 20,058-edge airport graph takes about 0.2 s.

Modularity is defined for undirected graphs, so a directed graph is first made
undirected by adding the weights of both directions. Edge weights are used
throughout.

## When to use it
For questions about group structure, and how strong that structure is:

- "What communities exist in this network, and how strong are they?"
- "Which airports fly mostly among themselves?"

`k_core` finds one dense core; this splits the *whole* graph into groups.
`connected_components` splits it where there are no links at all, which is a much
weaker condition.

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| resolution | number | 1.0 | Above 1 gives more, smaller communities; below 1 fewer, larger ones (0.01 to 100) |
| seed | integer | 0 | Fixes the order nodes are visited in, so results repeat |
| top_k | integer | 10 | How many communities to return, largest first (1 to 100) |

## Output
```json
{"communities_found": 4, "modularity": 0.41979, "resolution": 1.0, "seed": 0, "levels": 2,
 "largest_community_size": 12, "smallest_community_size": 5, "communities_shown": 4,
 "communities": [{"rank": 1, "size": 12, "internal_edges": 33, "graph_id": "karate~1",
                  "members": [{"id": "m34", "label": "Member 34 (president)", "links_inside": 11}]}]}
```

Communities are ranked largest first, ties broken by their smallest member id, and
each one is registered as its own graph whose id is in that entry. `result_graph_id`
is the largest community. `members` lists up to five of each community's best
connected members, where `links_inside` counts neighbours within the same community.
If the response would pass 8 KB, the member lists are shortened first and whole
communities dropped only after that, with `communities_shown` saying how many are
left.

## Graphs it supports
All of them: directed and undirected, weighted and unweighted. A directed graph is
treated as undirected with summed weights, so "communities of mutual traffic", not
of one-way flow. A graph with no edges is an error rather than a split into
singletons.

## Determinism
Louvain visits nodes in a shuffled order, which is where its randomness lies. The
order comes from `random.Random(seed)` with `seed=0` by default, and ties in the
modularity gain go to the lower community id, so the same call always returns the
same answer. Changing the seed is a good way to check how stable the communities
are; the modularity usually moves very little.

## Errors
| When | Message |
| --- | --- |
| Unknown `graph_id` | No graph with that id; use `list_graphs` |
| `resolution` not a number in 0 to 100 | Says the range and what 1.0 means |
| `seed` not a whole number | Says any whole number works |
| `top_k` outside 1 to 100 | Says the allowed range |
| Any other parameter | Lists the parameters the tool takes |
| Graph with no edges | Says there are no communities to find |
