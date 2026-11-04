
# Girvan-Newman

**Author:** afc500fb · **Tier:** hard · **Category:** community

## What it computes

The Girvan-Newman algorithm detects communities in an undirected graph.
It calculates edge betweenness, removes the edge with the highest score,
and recalculates the scores after every removal until the requested number
of connected components is reached or exceeded.

For an unweighted graph, edge betweenness measures how many shortest paths
between node pairs pass through an edge. This implementation treats every
edge as having unit length, even if the input graph stores weights.

Using Brandes' algorithm, calculating edge betweenness costs
O(VE) on an unweighted graph. Recomputing it after each edge removal makes
the overall worst-case cost approximately O(VE^2).

## When to use it

Use this tool to discover groups of densely connected nodes and identify
edges that connect different groups.

Example questions:
- "Find two communities in the karate club network."
- "Which connections are removed to separate this network into three groups?"

## Parameters

| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | required | Id of the graph |
| communities | integer | 2 | Target number of communities; must be at least 1 and no greater than the number of nodes |

## Output

`result` contains:
- `number_of_communities`: number of communities returned
- `communities`: each community's index, registered `graph_id`, size, and node references
- `removed_edges`: edges removed in order, with endpoint node references and their betweenness scores before removal

`result_graph_id` is the registered subgraph ID of the largest community.
If multiple communities tie for largest size, the one whose smallest node ID
comes first is selected.

## Graphs it supports

Supports undirected weighted and unweighted graphs. All edges are treated
as equal-length for edge betweenness. Directed graphs are rejected with an
error because this implementation uses the standard undirected procedure.

If the graph is already disconnected, the algorithm preserves its existing
components. If their count is already at least the requested target, no edges
are removed. Therefore, the actual community count may exceed the target.

Node IDs and ties are processed deterministically.

## Errors

The tool returns an error for:
- An unknown graph ID
- Unknown parameters
- A non-integer or less-than-one community target
- A target greater than the number of nodes
- A directed graph
- An empty graph
