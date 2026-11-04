# Louvain

**Author:** f1f54c61 · **Tier:** Hard · **Category:** Community and Structure

## What it computes

The Louvain algorithm detects communities in an undirected graph by optimizing modularity, a measure of how densely connected nodes are within communities compared with what would be expected from a random graph with similar degree distribution. It repeatedly moves nodes between communities to improve modularity and aggregates the resulting communities into supernodes for further optimization.

For a graph with \(V\) nodes and \(E\) edges, a typical implementation runs in approximately \(O(V\log V)\) time on sparse graphs in practice, although the worst-case complexity depends on the number of node-movement passes and aggregation levels. This implementation uses up to 100 local-movement passes per level and 20 aggregation levels.

## When to use it

Use Louvain to discover communities in undirected graphs, where nodes form groups with relatively dense internal connections. It supports both weighted and unweighted graphs, provided edge weights are finite and non-negative. Directed graphs are not supported.

It is useful for exploring community structure without specifying the number of communities in advance.

Example questions:
- Which groups of people form closely connected communities in an undirected social network?
- Which clusters of devices or entities are strongly connected in an undirected, weighted network?

## Parameters

| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| `graph_id` | string | (required) | ID of the input graph |
| `top_k` | integer | 10 | Maximum number of communities to return (1 to 100) |

## Output

The `result` field contains a list of community objects, ordered by descending community size and then by the smallest node ID. Each object contains:
- `community`: the community's rank in the returned list.
- `size`: the total number of nodes in the community.
- `nodes`: up to 10 node references, each containing an ID and label.
- `graph_id`: ID of the registered subgraph containing all nodes in that community.

The `summary` field reports the total number of communities, the number of graph nodes, the overall modularity score, and how many communities were returned.

The tool also returns `result_graph_id`, which identifies the subgraph for the largest community returned, or `null` if no community is returned.

Example `result`:

```json
[
  {
    "community": 1,
    "size": 3,
    "nodes": [
      {"id": "a", "label": "Node A"},
      {"id": "b", "label": "Node B"},
      {"id": "c", "label": "Node C"}
    ],
    "graph_id": "example~community1"
  }
]