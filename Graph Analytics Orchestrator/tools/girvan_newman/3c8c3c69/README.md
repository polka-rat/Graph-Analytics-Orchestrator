# girvan_newman

Author: 3c8c3c69 | Tier: hard | Category: community

## What it computes
Communities, found with the Girvan-Newman method:
1. Compute the betweenness of every edge (Brandes' algorithm).
2. Remove the edge with the highest betweenness.
3. Repeat. Each time the graph splits into one more part, that is a new level.

The tool returns the level with the highest modularity, or the first level with at least num_communities communities. Edge order and ties are handled the same way as networkx.community.girvan_newman, so the results match NetworkX.

Time complexity: O(m * n) per betweenness computation, up to m times, so O(m^2 * n) in the worst case. After each removal, betweenness is recomputed only in the part that changed.

## When to use it
- "How does the karate club break apart into groups?"
- "Split the club into its two factions." (num_communities = 2)

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| num_communities | integer | (none) | Stop at the first level with at least this many communities. If not given, the level with the highest modularity is returned |
| top_k | integer | 10 | How many of the largest communities to list (1 to 100) |

## Output
- num_communities, modularity and edges_removed for the level returned
- chosen_by: highest modularity or num_communities
- communities: the top_k largest communities, each with its size, graph_id and members (best-connected first)
- splits: the first 10 levels, each with its number of communities, edges removed, modularity and the sizes of the two new parts

Example (karate, num_communities 2):

```
{"num_communities": 2, "modularity": 0.359961, "edges_removed": 11, "chosen_by": "num_communities",
 "communities": [{"size": 19, "graph_id": "karate~1", "members": [...]},
                 {"size": 15, "graph_id": "karate~2", "members": [...]}],
 "splits": [{"num_communities": 2, "edges_removed": 11, "modularity": 0.359961, "split_sizes": [19, 15]}]}
```

result_graph_id is the largest community.

If the graph already has at least num_communities separate parts, those parts are returned and no edge is removed.

## Graphs it supports
- Undirected and directed graphs. Direction is ignored.
- Weighted and unweighted graphs. Weights are ignored.
- Disconnected graphs. Self-loops are ignored.
- Small graphs only. karate takes about 0.02 s and lesmis about 0.15 s. airports is too large, so the tool returns an error straight away.

## Errors
- Unknown graph_id
- Graph has no edges
- Graph too large for this method (suggests a smaller subgraph, louvain or label_propagation)
- Run stopped because it would take too long (suggests num_communities or a smaller subgraph)
- num_communities is not a whole number from 1 to the number of nodes
- top_k is not between 1 and 100
- Unknown extra parameter
