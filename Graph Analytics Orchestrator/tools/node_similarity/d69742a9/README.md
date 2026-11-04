# node_similarity

**Author:** d69742a9 · **Tier:** easy · **Category:** structure

## What it computes
It compares two nodes using the intersection and union of their neighbour sets. The Jaccard score is `|intersection| / |union|`; directed graphs use incoming and outgoing neighbours together. The running time is linear in the two neighbourhood sizes.

## When to use it
Use this tool for questions such as “How similar are Alice's and Bob's connections?” or “Which routes do these two airports share?”

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | required | Id of the graph |
| node | string | required | First node id |
| other | string | required | Second node id |

## Output
`result` contains node references, the common-neighbour references, their count, and the rounded Jaccard score. It does not create a subgraph.

## Graphs it supports
Directed and undirected, weighted and unweighted graphs. Edge weights are not used.

## Errors
It returns an error for an unknown graph or node, equal node ids, or unknown parameters.

