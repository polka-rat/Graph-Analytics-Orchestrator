# bipartite_matching

**Author:** 54d073a3 · **Tier:** hard · **Category:** structure

## What it computes
A maximum cardinality matching of a bipartite graph: the largest set of edges in which no node appears twice, found with the Hopcroft-Karp algorithm.

1. The graph is 2-coloured by breadth-first search. If an edge joins two nodes of the same colour (or a node has a self-loop) the graph is not bipartite and the tool returns an error naming the offending edge.
2. Hopcroft-Karp repeats two steps until no augmenting path exists: a breadth-first search layers the graph from the unmatched left nodes, then depth-first searches (implemented iteratively, so there is no recursion limit) augment along a maximal set of shortest vertex-disjoint augmenting paths.

Time $O(E\sqrt{V})$. The "left" side of each connected component is the colour of its smallest node id; this only fixes how pairs are printed and never changes the matching size.

## When to use it
- "What is the best assignment of students to projects?"
- "How many students can be given a project of their own?"
- "Which students are left without a project?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of a bipartite graph, e.g. `projects` |
| top_k | integer | 10 | How many matched pairs and unmatched nodes to list (1 to 100) |

## Output
`result` is an object:
- `matching_size`: number of matched pairs (the maximum possible).
- `is_perfect_matching`: true if every node is matched.
- `left_size`, `right_size`: sizes of the two sides.
- `num_unmatched`: how many nodes are not matched.
- `pairs`: up to `top_k` entries `{"left": {id, label}, "right": {id, label}}`, sorted by the left node id.
- `unmatched`: up to `top_k` nodes `{id, label, side}`, sorted by id.

If the lists would exceed the 8 KB limit they are shortened and the summary says so. The tool does not return `result_graph_id`.

## Graphs it supports
Bipartite graphs only. Directed graphs are accepted: direction is ignored and the underlying undirected graph is matched. Weights are ignored (maximum cardinality, not maximum weight). Isolated nodes are allowed and stay unmatched.

## Errors
- Unknown `graph_id`.
- `top_k` not a whole number from 1 to 100.
- The graph is not bipartite (the message names an edge that breaks it).
- Unknown parameter.
- A graph with no nodes.
