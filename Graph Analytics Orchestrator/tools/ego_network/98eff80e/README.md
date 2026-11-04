# ego_network

**Author:** 98eff80e · **Tier:** easy · **Category:** subgraph

## What it computes
The `ego_network` tool extracts the induced subgraph centered on a focal node (the *ego*) and its surrounding neighbours (*alters*) up to a given hop distance (`radius`). The algorithm performs a breadth-first search (BFS) starting from the center node up to `radius` hops, collects all reachable nodes, and registers the induced subgraph containing those nodes and all original edges connecting them into the `GraphStore`.

The time complexity is $O(V + E)$ where $V$ and $E$ are the number of nodes and edges explored within the specified hop radius. Space complexity is $O(V_{ego} + E_{ego})$ to store the induced subgraph.

## When to use it
Use this tool when an agent or user wants to inspect the local neighborhood, immediate surroundings, or community sphere of a specific entity in a network.

Example questions:
- "Show me Bob's immediate network."
- "What is the local subgraph around airport MAA?"
- "Which courses are direct or 2-hop prerequisites/follow-ups around CS201?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| `graph_id` | string | *(required)* | ID of the graph to analyse (e.g. `"karate"`, `"airports"`). |
| `node` | string | *(required)* | ID of the focal center node. Use `lookup_node` first if only a name is known. |
| `radius` | integer | `1` | Maximum hop distance from the center node to include (between 1 and 10). |
| `include_center` | boolean | `true` | Whether to include the center node itself in the ego network subgraph. |
| `undirected` | boolean | `false` | If `true` on directed graphs, traverse incoming and outgoing edges; if `false`, follow outgoing edges only. |
| `top_k` | integer | `10` | Maximum number of nodes in the ego network to preview in `result["nodes"]` (between 1 and 100). |

## Output
Returns `status: "ok"` with `result_graph_id` set to the newly registered subgraph ID (e.g., `"karate~1"` or `"airports~2"`). The `result` dictionary contains:
- `center`: Node reference object `{"id": ..., "label": ...}` for the focal center node.
- `radius`: Hop radius used (`int`).
- `include_center`: Whether the center was included in the induced subgraph (`bool`).
- `undirected`: Whether incoming edges were also followed on directed graphs (`bool`).
- `node_count`: Number of nodes in the induced ego subgraph (`int`).
- `edge_count`: Number of edges in the induced ego subgraph (`int`).
- `nodes`: List of up to `top_k` node references in the ego network, sorted by distance from center and node ID. Each node reference has `id`, `label`, `distance` (hops from center), and `degree_in_ego` (degree within the induced subgraph).

Example `result`:
```json
{
  "center": {
    "id": "m1",
    "label": "Member 1 (instructor)"
  },
  "radius": 1,
  "include_center": true,
  "undirected": false,
  "node_count": 17,
  "edge_count": 34,
  "nodes": [
    {
      "id": "m1",
      "label": "Member 1 (instructor)",
      "distance": 0,
      "degree_in_ego": 16
    },
    {
      "id": "m2",
      "label": "Member 2",
      "distance": 1,
      "degree_in_ego": 5
    }
  ]
}
```

## Graphs it supports
- **Undirected graphs** (e.g., `karate`, `lesmis`, `projects`): BFS explores all incident edges.
- **Directed graphs** (e.g., `airports`, `courses`): Follows outgoing edges (successors) by default (`undirected=false`), matching NetworkX `ego_graph`. When `undirected=true`, explores both incoming and outgoing edges.
- **Weighted and unweighted graphs**: Edge weights and attributes are preserved in the registered induced subgraph.

## Errors
The tool returns `status: "error"` without crashing in the following situations:
- Unknown `graph_id`: If the requested graph does not exist in `GraphStore`.
- Missing or unknown `node`: If `node` is omitted, not a string, or not present in the graph.
- Invalid `radius`: If `radius` is not an integer or not within `1 <= radius <= 10`.
- Invalid boolean flags: If `include_center` or `undirected` are not booleans.
- Invalid `top_k`: If `top_k` is not an integer between 1 and 100.
- Unknown parameter(s): If any unrecognised keyword arguments are passed.
