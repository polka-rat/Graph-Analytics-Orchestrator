# girvan_newman

**Author:** d35c782d · **Tier:** hard · **Category:** community

## What it computes
Girvan-Newman community detection. It repeatedly finds the edge that lies on the most shortest paths (the edge betweenness) and removes it, so the graph breaks into groups. Edge betweenness is computed with Brandes' method: a breadth-first search from every node counts the shortest paths to each node, and credit then flows back up the search tree, each node passing its credit (1 plus what it received) to its parent edges in proportion to their path counts. Only the component that lost an edge is recomputed. Every time the graph splits, the modularity of the new split is recorded, and the split with the highest modularity is returned (the first one on a tie), or the first split with `n_communities` groups if that is given. Time: one betweenness pass is O(n·m) (O(n·(m + n log n)) with weights), and up to m passes are needed, so O(m²·n) in the worst case.

## When to use it
Questions about groups in a small or medium network, for example "Which groups does the karate club split into?" or "Divide the Les Miserables characters into 5 communities." It is slow on large graphs: about 600 edges is the comfortable limit.

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| n_communities | integer | none | Number of communities wanted (2 or more). If left out, the split with the best modularity is returned |
| use_weights | boolean | false | true uses edge weights as distances (they must be above 0); false counts every edge the same |
| use_direction | boolean | false | For directed graphs: true follows edge direction for the shortest paths; false ignores it. Ignored on undirected graphs |
| top_k | integer | 10 | How many communities to list, largest first (1 to 100) |

## Output
`result` is a list of communities, largest first (ties by the smallest node id). Each entry has `community` (its rank), `graph_id` (the id of that community registered as a subgraph), `size`, `n_edges` (edges inside it) and `nodes` (every member as `{id, label}`; shortened only if the output would pass 8 KB). `result_graph_id` is the id of the largest community. The summary gives the number of communities, the modularity, how many edges were removed, and a warning for big graphs.

Example (karate, `n_communities=2`): `{"community": 1, "graph_id": "karate~1", "size": 19, "n_edges": 40, "nodes": [{"id": "m10", "label": "Member 10"}, ...]}`

## Graphs it supports
Directed and undirected, weighted and unweighted. By default every graph is treated as undirected and unweighted. Modularity is always computed on the graph as it is (weighted if the graph is weighted, directed formula if it is directed). A graph with more than 600 edges is still solved in full, but the summary warns that it may take more than 30 seconds. If the graph is already in separate pieces and `n_communities` is no larger than the number of pieces, the pieces are returned.

## Errors
- Unknown `graph_id`, or a graph with no nodes.
- `top_k` outside 1 to 100.
- `n_communities` that is not a whole number between 2 and the number of nodes.
- `use_weights` or `use_direction` that is not true or false.
- `use_weights` on a graph with an edge weight of 0 or less.
- Any unknown parameter.
