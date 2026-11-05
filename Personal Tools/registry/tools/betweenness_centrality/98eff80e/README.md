# betweenness_centrality

**Author:** 98eff80e · **Tier:** hard · **Category:** centrality

## What it computes

Betweenness centrality quantifies the extent to which a node lies on the shortest paths between all pairs of nodes in a network. This implementation uses Ulrik Brandes' exact shortest-path algorithm (Brandes, 2001), running in $O(V \cdot E)$ time for unweighted networks (using Breadth-First Search) and $O(V \cdot E + V^2 \log V)$ time for weighted networks (using Dijkstra's algorithm with binary min-heaps).

Shortest paths are identified from every source node $s \in V$, predecessor DAGs and path counts $\sigma$ are tracked, and pair dependencies $\delta$ are accumulated in reverse topological order of path distances.

## When to use it

Use this tool to find critical brokers, bottlenecks, liaisons, or single points of failure in a graph:
- *"Who are the key brokers or intermediaries bridging different factions in the network?"*
- *"Which hub airports carry the highest fraction of all shortest connecting flight routes?"*
- *"Which prerequisite courses are unavoidable chokepoints in the academic curriculum?"*

## Parameters

| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| `graph_id` | `string` | *(required)* | Identifier of the graph in the store (e.g. `"karate"`, `"airports"`). |
| `top_k` | `integer` | `10` | Maximum number of highest-scoring nodes to return (integer from 1 to 100). |
| `normalized` | `boolean` | `true` | When `true`, divides raw scores by the number of possible $(s, t)$ node pairs ($N(N-1)$ for directed, $N(N-1)/2$ for undirected). |
| `weighted` | `boolean` | `false` | When `true`, uses positive edge weights as physical distances (Dijkstra); when `false`, counts hop count (BFS). |
| `endpoints` | `boolean` | `false` | When `true`, includes start $s$ and end $t$ endpoints in the path counts. |

## Output

Returns a JSON object conforming to the GraphKit tool contract:
- `status`: `"ok"` on success, `"error"` on invalid input.
- `result`: A list of up to `top_k` node references, sorted deterministically by descending score (with ties broken by ascending node ID). Each item contains `id`, `label`, and `score` (rounded to 6 decimal places).
- `summary`: A natural language summary highlighting the top-scoring node and graph statistics.
- `result_graph_id`: `null` (centrality metrics evaluate existing graph nodes without creating new subgraphs).

Example result:
```json
{
  "status": "ok",
  "result": [
    {"id": "m1", "label": "Member 1 (instructor)", "score": 0.437635},
    {"id": "m34", "label": "Member 34 (admin)", "score": 0.304075},
    {"id": "m33", "label": "Member 33", "score": 0.145247}
  ],
  "summary": "Computed betweenness centrality for 34 nodes in 'karate'. Member 1 (instructor) (m1) has the highest score (0.437635).",
  "result_graph_id": null,
  "error": null
}
```

## Graphs it supports

- **Directed and Undirected:** Fully supports both directed (DAGs, route networks) and undirected networks. Directed graphs follow edge direction for paths and normalize by $N(N-1)$. Undirected graphs normalize by $N(N-1)/2$.
- **Weighted and Unweighted:** Supports unweighted graphs via BFS and weighted graphs via Dijkstra's algorithm. In weighted mode, edge weights represent distance/cost and must be strictly positive ($w > 0$).
- **Disconnected Graphs & Subgraphs:** Correctly handles disconnected components, isolates, and single-node subgraphs ($N < 2$, returning score `0.0`).

## Errors

The tool returns `{"status": "error", "result": None, "error": "<message>"}` in the following cases:
- Unknown `graph_id`: The requested graph does not exist in the store.
- Invalid `top_k`: Value is not an integer between 1 and 100.
- Invalid boolean arguments: `normalized`, `weighted`, or `endpoints` is not a boolean.
- Unknown extra parameters: Unexpected keyword arguments are rejected.
- Non-positive edge weights: If `weighted=True` and any edge has weight $\le 0.0$.
