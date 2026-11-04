# max_flow_min_cut

Author: [ANONYMOUS] (3ddaa37e)

Computes maximum flow and a minimum cut between distinct source and sink nodes using Edmonds-Karp. Use for capacity and bottleneck questions on directed or undirected graphs. Treats finite nonnegative edge weights as capacities; unweighted edges have capacity 1. Returns flow value, cut capacity and bounded previews of cut edges and both partitions. Distance weights are not physical transport capacities.

## Parameters

- `graph_id`: ID of the graph to analyse.
- `top_k`: Maximum entries in each output preview. Full scalar totals are unaffected.
- `source`: Exact source node ID. Resolve names with lookup_node.
- `sink`: Exact sink node ID. Resolve names with lookup_node.

## Output and limits

Returns the standard five-key contract. Every node has an ID and label. Floating results are rounded to six places. Lists are previews bounded by top_k and the 8 KB limit; counts and totals describe the full computation. A truncated flag reports omitted preview entries. BFS visits neighbors in ascending node ID order.

## Errors

Unknown graphs, unknown parameters, invalid top_k and unsupported inputs return helpful errors. See the description above for graph restrictions. Tools do not change their input graph, print, access files or make network requests.

## Algorithm and complexity

Run BFS in the residual network, augment by the smallest residual capacity on the path and update reverse capacities. When the sink is unreachable, residual-reachable nodes define the source side of the cut. Opposite original edges share residual entries correctly. An undirected edge provides equal capacity in either direction; self-loops do not affect transfer. No path gives zero flow. Time O(V E^2), space O(V + E).

## Checking

Run the validator and pytest from the starter root. NetworkX is used only in tests.

## Example questions

- What is the maximum flow from CS101 to CS401?
- Which edges form a minimum cut between these nodes?

## Example call and output

Input:

```json
{"graph_id": "courses", "source": "CS101", "sink": "CS401"}
```

Output fields: source, sink, max_flow, cut_capacity, cut_edges, source_side, sink_side, their full counts and truncated. All node references include id and label.

The following is a short example:

```json
{
  "status": "ok",
  "result": {
    "source": {
      "id": "CS101",
      "label": "Programming Basics"
    },
    "sink": {
      "id": "CS401",
      "label": "Distributed Systems"
    },
    "max_flow": 2.0,
    "cut_capacity": 2.0,
    "cut_edges": [
      {
        "source": {
          "id": "CS101",
          "label": "Programming Basics"
        },
        "target": {
          "id": "CS102",
          "label": "Data Structures"
        },
        "capacity": 1.0
      },
      {
        "source": {
          "id": "CS101",
          "label": "Programming Basics"
        },
        "target": {
          "id": "CS202",
          "label": "Computer Organisation"
        },
        "capacity": 1.0
      }
    ],
    "source_side": [
      {
        "id": "CS101",
        "label": "Programming Basics"
      }
    ],
    "sink_side": [
      {
        "id": "CS102",
        "label": "Data Structures"
      },
      {
        "id": "CS201",
        "label": "Algorithms"
      },
      {
        "id": "CS202",
        "label": "Computer Organisation"
      },
      {
        "id": "CS203",
        "label": "Theory of Computation"
      },
      {
        "id": "CS301",
        "label": "Operating Systems"
      },
      {
        "id": "CS302",
        "label": "Databases"
      },
      {
        "id": "CS303",
        "label": "Computer Networks"
      },
      {
        "id": "CS304",
        "label": "Compilers"
      },
      {
        "id": "CS305",
        "label": "Machine Learning"
      },
      {
        "id": "CS306",
        "label": "Graph Algorithms"
      }
    ],
    "source_side_count": 1,
    "sink_side_count": 20,
    "cut_edge_count": 2,
    "truncated": true
  },
  "summary": "Maximum flow is 2.000000, and minimum-cut capacity is 2.000000. Edge weights are treated as capacities; unweighted edges have capacity 1.",
  "result_graph_id": null,
  "error": null
}
```

Parameter types and defaults: graph_id is a required string. top_k is an integer with default 10, minimum 1 and maximum 100. source and sink are required strings.
