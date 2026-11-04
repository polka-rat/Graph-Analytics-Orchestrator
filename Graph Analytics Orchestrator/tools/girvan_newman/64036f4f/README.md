# girvan_newman

**Author:** Hayagriv (64036f4f) · **Tier:** hard · **Category:** community

## What it computes

This tool calculates unweighted edge betweenness with Brandes' algorithm, removes the highest-scoring edge, and repeats until the requested number of connected components exists. Edge-score ties use ascending endpoint ids, so results are deterministic. Its worst-case complexity is O(EVE), appropriate for the assignment's small community datasets.

## When to use it

Use it for questions such as “How does the karate network split into two groups?” or “What three communities appear in the Les Misérables network?”

## Parameters

| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | required | Id of an undirected graph |
| num_communities | integer | 2 | Target community count, from 2 to 20 |

## Output

`result.communities` lists each community's size, node references, and registered induced-subgraph id. `result.modularity` reports the partition's unweighted modularity. The largest community's id is returned as `result_graph_id`.

## Graphs it supports

Undirected weighted or unweighted graphs are supported; weights are ignored by the community algorithm. Directed graphs return an error.

## Errors

The tool returns guidance for unknown graphs, directed graphs, invalid community counts, impossible counts, unsupported parameters, and inputs that start with more connected components than requested.
