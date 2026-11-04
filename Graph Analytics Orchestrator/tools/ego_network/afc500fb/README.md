
# ego_network

**Author:** afc500fb · **Tier:** easy · **Category:** subgraph

## What it computes

Extracts the one-hop ego network of a specified node. The output contains the ego, all direct neighbors, and every original edge among the selected nodes. Finding the neighbors takes O(V) time in the worst case with the current graph interface; registering the induced subgraph scans the graph's edges, taking O(V + E) time.

## When to use it

Use this tool to inspect the immediate neighborhood of a node.

Example questions:
- Which nodes are directly connected to node MAA?
- What does the local network around a particular person look like?

## Parameters

| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | ID of the graph |
| node | string | (required) | ID of the ego node |

## Output

Returns the ego node, direct neighbors, all selected nodes, node count, and edge count. The induced subgraph is registered in the graph store and its ID is returned as `result_graph_id`.

## Graphs it supports

Supports directed and undirected, weighted and unweighted graphs. For directed graphs, incoming and outgoing neighbors are both included, while the resulting subgraph retains the original edge directions and weights.

## Errors

- Unknown graph ID: use `list_graphs` to see available graph IDs.
- Unknown or invalid node ID: use `lookup_node` to find valid node IDs.
- Unsupported parameter: remove the parameter and use `graph_id` and `node`.
