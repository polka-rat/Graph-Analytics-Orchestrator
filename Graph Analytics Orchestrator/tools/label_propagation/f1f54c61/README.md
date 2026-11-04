# Label_Propagation

**Author:** f1f54c61 · **Tier:** Medium · **Category:** Community and Structure

## What it computes

Label Propagation detects communities by assigning each node a label and repeatedly updating it to the most frequent label among its neighbors. The process continues until labels converge or the maximum number of iterations is reached. For a graph with \(V\) nodes and \(E\) edges, each iteration takes approximately \(O(V+E)\) time, giving an overall complexity of \(O(I(V+E))\), where \(I\) is the number of iterations.

## When to use it

Use Label Propagation to identify groups of densely connected nodes in directed or undirected graphs with support for both weighted and unweighted graphs. It is useful when you want to discover communities quickly without specifying their number in advance.

Example questions:
- Which groups of users form communities in a social network?
- Which clusters of airports or other entities are connected by stronger relationships?

## Parameters

| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| `graph_id` | string | (required) | ID of the input graph |
| `top_k` | integer | 10 | Maximum number of communities to return (1 to 100) |

## Output

The `result` field contains a list of community objects, ordered by descending community size. Each object contains:
- `community`: the community's rank in the returned list.
- `size`: the total number of nodes in the community.
- `nodes`: up to 10 node references, each containing an ID and label.
- `graph_id`: ID of the registered subgraph containing all nodes in that community.

The `summary` field reports the number of detected communities, the number of graph nodes, the iteration count, whether labels converged, and how many communities were returned.

The tool also returns `result_graph_id`, identifying the subgraph for the largest community returned, or `null` if no community is returned.

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