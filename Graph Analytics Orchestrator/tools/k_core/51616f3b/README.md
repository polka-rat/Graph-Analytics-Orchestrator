# k_core

Author: 51616f3b
Tier: medium
Category: community

## Definitions
- A **k-core** is the maximal induced subgraph in which every vertex has degree at least $k$ within that subgraph.
- A node's **core number** is the highest integer $k$ such that the node belongs to a $k$-core.
- The **densest core** (or main core) refers to the $k$-core for the maximum core number present in the graph.

## Algorithm
This tool implements the Batagelj-Zaversnik $O(n + m)$ bucket-sorting algorithm:
1. Nodes are ordered and initial degrees are calculated.
2. Nodes are placed into bins corresponding to their degrees using counting sort.
3. The vertex with the smallest degree is processed iteratively: for each of its higher-degree neighbors, their degrees are decremented and their positions in the bin array are updated.
4. When finished, the final degrees in the array represent the exact core numbers for all nodes.

## Modes and weights
Edge weights are always ignored. On directed graphs, two modes are supported:
- `total` (default): Degree is calculated as in-degree + out-degree. Reciprocal pairs count twice, matching NetworkX's `core_number` on directed graphs.
- `undirected`: The directed graph is treated as a simple undirected graph by ignoring edge direction and collapsing reciprocal pairs into a single link.

The registered subgraph always keeps the parent graph's direction and attributes.

## Parameters
- `graph_id` (string, required): ID of the graph to analyse.
- `k` (integer, optional): The core level to extract. If omitted, it defaults to the maximum core number (the densest core). Must be non-negative and $\le$ max core. Setting $k=0$ selects all nodes.
- `top_k` (integer, optional, default 10, max 100): Maximum number of top nodes to display in the preview.
- `mode` (string, optional, default "total"): "total" or "undirected".

## Output preview
The `top_nodes` list returns up to `top_k` nodes, ordered descending by `core_number`, with ties broken by ascending node ID. In the example below, all 10 nodes share core number 4 and are ordered lexicographically by node ID: `m1`, `m14`, `m2`, `m3`, etc.

## Output example
```json
{
  "status": "ok",
  "result": {
    "selected_k": 4,
    "max_core_number": 4,
    "mode": "total",
    "selected_node_count": 10,
    "selected_edge_count": 25,
    "density": 0.555556,
    "component_count": 1,
    "core_distribution": {
      "1": 1,
      "2": 11,
      "3": 12,
      "4": 10
    },
    "top_nodes": [
      {
        "id": "m1",
        "label": "Member 1 (instructor)",
        "core_number": 4,
        "in_selected_core": true
      },
      {
        "id": "m14",
        "label": "Member 14",
        "core_number": 4,
        "in_selected_core": true
      },
      {
        "id": "m2",
        "label": "Member 2",
        "core_number": 4,
        "in_selected_core": true
      },
      {
        "id": "m3",
        "label": "Member 3",
        "core_number": 4,
        "in_selected_core": true
      },
      {
        "id": "m31",
        "label": "Member 31",
        "core_number": 4,
        "in_selected_core": true
      },
      {
        "id": "m33",
        "label": "Member 33",
        "core_number": 4,
        "in_selected_core": true
      },
      {
        "id": "m34",
        "label": "Member 34 (administrator)",
        "core_number": 4,
        "in_selected_core": true
      },
      {
        "id": "m4",
        "label": "Member 4",
        "core_number": 4,
        "in_selected_core": true
      },
      {
        "id": "m8",
        "label": "Member 8",
        "core_number": 4,
        "in_selected_core": true
      },
      {
        "id": "m9",
        "label": "Member 9",
        "core_number": 4,
        "in_selected_core": true
      }
    ],
    "preview_truncated": true
  },
  "summary": "4-core of 'karate' (mode=total) has 10 nodes, 25 edges, 1 component(s), density 0.555556; max core is 4 (preview shows 10 of 34 nodes).",
  "result_graph_id": "karate~1",
  "error": null
}
```

## What result_graph_id means
The tool extracts all nodes with core number $\ge k$ and registers their induced subgraph in the graph store. Downstream tools can use this registered ID to run further algorithms on the isolated core.

## Time complexity
The Batagelj-Zaversnik algorithm runs in $O(n + m)$ time, where $n$ is the number of nodes and $m$ is the number of edges. Component extraction via BFS runs in $O(n_{core} + m_{core})$. Sorting nodes for preview takes $O(n \log n)$. The entire process completes in under 1 second on all provided datasets.

## Errors
- Unknown graph ID: returns an error instructing the user to check `list_graphs`.
- Empty graph: returns an error indicating the graph is empty.
- Self-loops: returns an error if any self-loop is detected.
- $k > \text{max core}$: returns an error stating that $k$ exceeds the maximum core number and indicates the maximum value.
- Invalid $k$: returns an error if $k$ is negative, non-integer, or a boolean.
- Invalid mode: returns an error listing the allowed modes ("total", "undirected").
- Invalid top_k: returns an error if top_k is not an integer between 1 and 100.

## Running tests
From the repository root:
```bash
python -m pytest registry/tools/k_core/51616f3b/tests
python -m graphkit.validate registry/tools/k_core/51616f3b
```
