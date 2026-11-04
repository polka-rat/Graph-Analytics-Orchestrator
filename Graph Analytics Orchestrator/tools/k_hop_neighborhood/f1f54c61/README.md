# k_hop_neighborhood

**Author:** f1f54c61 · **Tier:** easy · **Category:** subgraph

## What it computes

The tool uses Breadth-First Search (BFS) to find all nodes within at most `k` hops of a specified starting node, including the starting node at distance 0. It records each selected node's shortest hop distance and registers the induced subgraph containing all selected nodes and every original edge between them. The time complexity is \(O(V+E+R\log R)\), where \(V\) and \(E\) are the input graph's node and edge counts, and \(R\) is the number of selected nodes.

## When to use it

Use this tool to identify nodes within a specified number of steps from a starting node.

Example questions:
- Who is within two hops of Alice?
- Which nodes can be reached from node `m1` within one hop?

## Parameters

| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| `graph_id` | string | (required) | ID of the graph to analyse. |
| `node` | string | (required) | ID of the starting node. |
| `k` | integer | 2 | Maximum number of hops from the starting node; must be non-negative. |

## Output

The `result` object contains:
- `start_node`: the starting node's ID and label.
- `k`: the requested hop limit.
- `nodes`: the selected nodes, each with its ID, label, and shortest distance from the starting node.
- `node_count`: the number of selected nodes.

The tool also returns `summary` and `result_graph_id`. The latter identifies the registered induced subgraph.

Example result:

```json
{
  "start_node": {"id": "m1", "label": "Example node"},
  "k": 1,
  "nodes": [
    {"id": "m1", "label": "Example node", "distance": 0},
    {"id": "m2", "label": "Another node", "distance": 1}
  ],
  "node_count": 2
}