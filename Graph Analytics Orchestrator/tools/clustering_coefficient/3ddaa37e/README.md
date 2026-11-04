# clustering_coefficient

Author: [ANONYMOUS] (3ddaa37e)

Computes ordinary unweighted local clustering and the mean over all nodes of an undirected graph. Use to ask how tightly connected a node's neighbors are. Ignores weights and self-loops; nodes with fewer than two neighbors have coefficient zero. Returns one specified node or top_k nodes with coefficients, plus the graph average. Rejects directed or empty graphs.

## Parameters

- `graph_id`: ID of the graph to analyse.
- `top_k`: Maximum entries in each output preview. Full scalar totals are unaffected.
- `node`: Optional exact node ID for a local coefficient; omit to rank nodes.

## Output and limits

Returns the standard five-key contract. Every node has an ID and label. Floating results are rounded to six places. Lists are previews bounded by top_k and the 8 KB limit; counts and totals describe the full computation. A truncated flag reports omitted preview entries. Equal coefficients are ordered by ascending node ID.

## Errors

Unknown graphs, unknown parameters, invalid top_k and unsupported inputs return helpful errors. See the description above for graph restrictions. Tools do not change their input graph, print, access files or make network requests.

## Algorithm and complexity

For each node, count edges between its distinct neighbors and divide by the number of possible pairs. Isolated nodes contribute zero to the mean. Uses adjacency-set intersections; a conservative time bound is O(V E), with O(V + E) temporary space.

## Checking

Run the validator and pytest from the starter root. NetworkX is used only in tests.

## Example questions

- How closely connected are the instructor's friends?
- What is the average clustering of the karate graph?

## Example call and output

Input:

```json
{"graph_id": "karate", "node": "m1"}
```

Output fields: nodes, average_clustering, node_count, weighted and truncated. Each node entry contains id, label and coefficient.

The following is a short example:

```json
{
  "status": "ok",
  "result": {
    "nodes": [
      {
        "id": "m1",
        "label": "Member 1 (instructor)",
        "coefficient": 0.15
      }
    ],
    "average_clustering": 0.570638,
    "node_count": 34,
    "weighted": false,
    "truncated": false
  },
  "summary": "Average clustering is 0.570638 across 34 nodes. Edge weights and self-loops are ignored.",
  "result_graph_id": null,
  "error": null
}
```

Parameter types and defaults: graph_id is a required string. top_k is an integer with default 10, minimum 1 and maximum 100. node is an optional string.
