# ego_network

Author: 51616f3b
Tier: easy
Category: subgraph

## What it computes
This tool extracts the ego network (1-hop neighborhood) around a given central node. It finds direct neighbors of the center node based on the chosen direction and builds an induced subgraph containing the center and those neighbors. Because the subgraph is induced, all original edges among the selected nodes are preserved.

The tool computes the total node count, edge count, graph density, and (for directed graphs) the number of reciprocal edge pairs. It ranks neighbors by their local degree inside the ego subgraph and returns the top ones in a preview list.

## Supported graphs
- Undirected graphs (such as karate, lesmis, projects).
- Directed graphs (such as airports, courses).
- Weighted and unweighted graphs. Original edge weights and attributes are preserved in the registered subgraph.

## Direction and weights
The `direction` parameter controls which neighbors are selected:
- `out` (default): selects outgoing neighbors (successors).
- `in`: selects incoming neighbors (predecessors).
- `both`: selects the union of incoming and outgoing neighbors.

For undirected graphs, all three options select the same neighbors. A `direction_note` field is included in every successful response explaining these definitions. Edge weights and node/edge attributes are retained in the induced subgraph.

## Parameters
- `graph_id` (string, required): ID of the graph to analyse.
- `node` (string, required): Exact ID of the center node. Use `lookup_node` first if you only have a name.
- `direction` (string, optional, default "out"): Neighbor direction to follow ("out", "in", or "both").
- `top_k` (integer, optional, default 10, max 100): Maximum number of top neighbors to include in the preview. Note that the 8192-byte response limit can automatically shorten this preview list.

## Output preview
The `neighbors_preview` list returns up to `top_k` neighbors, sorted by their local degree inside the ego subgraph in descending order, with ties broken by ascending node ID. If the response approaches the 8192-byte limit, the tool automatically trims the preview list to guarantee contract compliance and sets `preview_truncated` to true.

## Output example
```json
{
  "status": "ok",
  "result": {
    "center": {
      "id": "m1",
      "label": "Member 1 (instructor)"
    },
    "direction": "out",
    "direction_note": "'out' selects outgoing neighbours, 'in' selects incoming neighbours, and 'both' selects their union. For undirected graphs, all three options select the same neighbours.",
    "neighbor_count": 16,
    "node_count": 17,
    "edge_count": 34,
    "density": 0.25,
    "reciprocal_pair_count": null,
    "neighbors_preview": [
      {
        "id": "m2",
        "label": "Member 2",
        "local_degree": 8
      },
      {
        "id": "m3",
        "label": "Member 3",
        "local_degree": 6
      },
      {
        "id": "m4",
        "label": "Member 4",
        "local_degree": 6
      },
      {
        "id": "m14",
        "label": "Member 14",
        "local_degree": 4
      },
      {
        "id": "m8",
        "label": "Member 8",
        "local_degree": 4
      },
      {
        "id": "m11",
        "label": "Member 11",
        "local_degree": 3
      },
      {
        "id": "m5",
        "label": "Member 5",
        "local_degree": 3
      },
      {
        "id": "m6",
        "label": "Member 6",
        "local_degree": 3
      },
      {
        "id": "m7",
        "label": "Member 7",
        "local_degree": 3
      },
      {
        "id": "m13",
        "label": "Member 13",
        "local_degree": 2
      }
    ],
    "preview_truncated": true
  },
  "summary": "Ego network of Member 1 (instructor) (m1) has 16 neighbors, 17 nodes, and 34 edges with density 0.250000 (preview shows 10 of 16 neighbors).",
  "result_graph_id": "karate~1",
  "error": null
}
```

## What result_graph_id means
The tool registers the induced subgraph with the graph store and returns its ID in `result_graph_id` (e.g. `karate~1`). Downstream tools can pass this ID as `graph_id` to run further algorithms on the isolated ego network.

## Time complexity
Extracting neighbors takes $O(d)$ time where $d$ is the center node's out-degree, in-degree, or total degree depending on `direction`. Registering the induced subgraph takes $O(k + m_{sub})$, where $k$ is the number of nodes in the ego network and $m_{sub}$ is the number of induced edges among them. Computing local degrees takes $O(m_{sub})$. Sorting the neighbors for preview takes $O(k \log k)$. The overall time complexity is $O(d + m_{sub} + k \log k)$, running in under 0.1 seconds on all datasets.

## Errors
- Unknown graph ID: returns an error telling the user to use `list_graphs`.
- Unknown node ID or missing node: returns an error telling the user to use `lookup_node`.
- Invalid direction: returns an error listing the accepted values ("out", "in", "both").
- Invalid top_k: returns an error if top_k is not an integer between 1 and 100.
- Unknown parameters: returns an error listing the unrecognized parameter names.

## Running tests
From the repository root:
```bash
python -m pytest registry/tools/ego_network/51616f3b/tests
python -m graphkit.validate registry/tools/ego_network/51616f3b
```
