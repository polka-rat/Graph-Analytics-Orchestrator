# Girvan–Newman Community Detection

**Author:** 80ae2fd8 · **Tier:** Hard · **Category:** Community

## What it computes

This tool detects communities in an undirected graph using the Girvan–Newman algorithm. It repeatedly calculates edge betweenness centrality, removes the edge with the highest score, and recalculates the connected components until the requested number of communities is reached or no edges remain.

For a graph with \(n\) nodes and \(m\) edges, calculating edge betweenness using Brandes' algorithm takes \(O(nm)\) time. Recomputing it after each edge removal can make the overall algorithm computationally expensive.

## When to use it

Use this tool to identify groups of nodes that are more strongly connected internally than they are to the rest of the graph.

Example questions:
- Which communities exist in a social network?
- How can a network be divided into groups by removing important connecting edges?

## Parameters

| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | Required | ID of the graph to analyse |
| top_k | integer | 10 | Maximum number of communities returned and maximum number of node references displayed per community (1–100) |
| num_communities | integer | 2 | Target number of communities to detect (1–100) |

## Output

The `result` field contains a list of detected communities. Each community includes its index, registered subgraph ID, total number of nodes, displayed node references, and the number of omitted nodes.

The tool also returns `result_graph_id`, which identifies the subgraph corresponding to the largest returned community.

Example of the output structure:

json
{
  "community": 1,
  "graph_id": "generated_subgraph_id",
  "size": 5,
  "nodes": [
    {"id": "node1", "label": "Node 1"}
  ],
  "omitted_nodes": 4
}

The example illustrates the structure; the actual node IDs and subgraph IDs depend on the input graph.

## Graphs it supports

- **Directed graphs:** Not supported. The tool returns an error.
- **Undirected graphs:** Supported.
- **Weighted graphs:** Edge weights are ignored; the graph is treated as unweighted.
- **Empty graphs:** Supported; the tool returns an empty result with a summary message.

## Errors

The tool returns an error when:
- The specified graph does not exist or cannot be retrieved.
- `top_k` is not an integer in the permitted range of 1–100.
- `num_communities` is not an integer in the permitted range of 1–100.
- The input graph is directed.
- An unexpected parameter is supplied.
- A detected community cannot be registered as a subgraph.
