# girvan_newman

**Author:** 3237bc9e · **Tier:** hard · **Category:** community

## What it computes
Communities by the Girvan-Newman method: compute edge betweenness (Brandes' algorithm), remove the highest edge, and repeat; each time the graph falls into one more component is a level of the hierarchy. It returns the level with the highest modularity, or the first level with `num_communities` communities. One betweenness pass is O(n*m) and up to m edges are removed, so O(n*m^2) overall; graphs too large to finish in time (such as `airports`) get an error.

## When to use it
How a small network breaks apart into groups.
- "How does the karate club split into two factions?" (`num_communities=2`)
- "What are the communities among the characters of Les Miserables?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| num_communities | integer | none | Stop at the first level with this many communities; leave out for the highest modularity |
| top_k | integer | 10 | How many of the largest communities to list (1 to 100) |

## Output
`community_count`, `modularity` and `communities` (the `top_k` largest, each with `rank`, `size`, `graph_id`, up to 10 `members` and `more_members`). `result_graph_id` is the largest community.

```json
{"community_count": 2, "modularity": 0.359961,
 "communities": [{"rank": 1, "size": 19, "graph_id": "karate~1", "members": ["..."], "more_members": 9},
                 {"rank": 2, "size": 15, "graph_id": "karate~2", "members": ["..."], "more_members": 5}]}
```

## Graphs it supports
Small undirected graphs; directed graphs are treated as undirected. Weights are not used to pick edges but are used in modularity. A graph with no edges returns each node as its own community.

## Errors
Unknown `graph_id`; graph too large (suggests `louvain`, `label_propagation` or a subgraph); `num_communities` not a whole number from 1 to the number of nodes, or fewer than the existing components; `top_k` not a whole number from 1 to 100; unknown parameters.
