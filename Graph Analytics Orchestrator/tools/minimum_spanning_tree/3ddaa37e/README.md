# minimum_spanning_tree

Author: [ANONYMOUS] (3ddaa37e)

Finds a minimum-weight spanning tree using Kruskal and Union-Find. Use to connect every node at minimum total cost. Supports connected undirected graphs, including negative weights; unweighted edges cost 1. Returns total weight and a bounded edge preview, with the complete tree registered as result_graph_id. Rejects disconnected, directed or empty graphs.

## Parameters

- `graph_id`: ID of the graph to analyse.
- `top_k`: Maximum entries in each output preview. Full scalar totals are unaffected.

## Output and limits

Returns the standard five-key contract. Every node has an ID and label. Floating results are rounded to six places. Lists are previews bounded by top_k and the 8 KB limit; counts and totals describe the full computation. A truncated flag reports omitted preview entries. Equal weights are ordered by ascending endpoint IDs.

## Errors

Unknown graphs, unknown parameters, invalid top_k and unsupported inputs return helpful errors. See the description above for graph restrictions. Tools do not change their input graph, print, access files or make network requests.

## Algorithm and complexity

Sort edges by weight and endpoint IDs. Add an edge only when its endpoints belong to different Union-Find components. Ignore self-loops. Reject disconnected graphs instead of silently returning a forest. Time O(E log E + V); space O(V + E). A single node has a zero-edge, zero-weight tree.

## Checking

Run the validator and pytest from the starter root. NetworkX is used only in tests.

## Example questions

- What is the cheapest way to connect every character in this graph?
- What is the total weight of the minimum spanning tree?

## Example call and output

Input:

```json
{"graph_id": "lesmis"}
```

Output fields: edges, total_weight, node_count, edge_count and truncated. Each edge contains source and target node references and weight. The full tree ID is in result_graph_id.

The following is a short example (only the first edge is shown):

```json
{
  "status": "ok",
  "result": {
    "edges": [
      {
        "source": {
          "id": "c01",
          "label": "Anzelma"
        },
        "target": {
          "id": "c59",
          "label": "MmeThenardier"
        },
        "weight": 1.0
      }
    ],
    "total_weight": 105.0,
    "node_count": 77,
    "edge_count": 76,
    "truncated": true
  },
  "summary": "The minimum spanning tree connects 77 nodes with 76 edges and total weight 105.000000. The registered graph contains the full tree.",
  "result_graph_id": "lesmis~1",
  "error": null
}
```

Parameter types and defaults: graph_id is a required string. top_k is an integer with default 10, minimum 1 and maximum 100.
