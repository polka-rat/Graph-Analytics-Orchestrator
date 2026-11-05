# Diameter and eccentricity

Author: ab9fb3a3 · Tier: medium · Category: paths

Runs BFS from every node for hop distances, or Dijkstra from every node when use_weights=true. A node's eccentricity is its greatest shortest-path distance to any node. Diameter is the maximum eccentricity, radius the minimum; centre and periphery contain nodes attaining the radius and diameter respectively.

Use for: “How many hops separate the most distant people?” or “Which nodes form the centre of the network?”

| Parameter | Default | Meaning |
| --- | --- | --- |
| graph_id | required | Registered graph ID |
| top_k | 10 | 1–100 entries per returned list |
| use_weights | false | Count hops, or use edge weights as distances |

Supports nonempty connected undirected graphs and strongly connected directed graphs. Directed distances follow outgoing edges. Weighted graphs default to hops; weighted mode accepts finite non-negative weights, including zero. A single-node graph has radius and diameter 0. Disconnected graphs produce a helpful error, rather than silently discarding unreachable nodes.

`result` contains diameter, radius, use_weights, node_count, eccentricities (labelled nodes with eccentricity, descending by distance then ascending ID), center, center_count, periphery, periphery_count and truncated. Centre and periphery sort by ID. Each list is limited independently by top_k. Metrics and counts use the whole graph. Distances round to six decimals after calculation; extremal sets use unrounded distances. No result subgraph is registered.

For a three-node path a–b–c: diameter=2, radius=1, centre={b}, periphery={a,c}.

Complexity: BFS O(V(V+E)); Dijkstra O(V(V+E) log V) for simple graphs. Additional memory is O(V+E), since only one source's distances are retained at a time.

Errors: unknown/empty/disconnected graph, non-boolean use_weights, negative/non-finite weighted distances, distance overflow, invalid top_k, unknown parameters or output exceeding 8 KB. Choose a component, disable weights, or lower top_k as appropriate.

```sh
.venv/bin/python run_tool.py registry/tools/diameter_eccentricity/ab9fb3a3 graph_id=karate
.venv/bin/python -m pytest registry/tools/diameter_eccentricity/ab9fb3a3/tests
```
