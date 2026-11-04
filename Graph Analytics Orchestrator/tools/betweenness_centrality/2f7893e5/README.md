# betweenness_centrality

**Author:** 2f7893e5 · **Tier:** hard · **Category:** centrality

## What it computes
The betweenness centrality of every node: for each pair of other nodes (s, t), the fraction of shortest s→t paths that pass through the node, summed over all pairs. High betweenness marks a broker or bottleneck that sits between parts of the network.

It uses **Brandes' algorithm**. From every source s:
1. Find the shortest paths and count them. In the default mode this is a **BFS**. With `weighted=true` it is **Dijkstra** with a heap. For every node w the search records σ(w), the number of shortest s→w paths, and the predecessors of w on those paths.
2. Walk the nodes in order of decreasing distance and accumulate dependencies: δ(v) += σ(v)/σ(w) · (1 + δ(w)) for each predecessor v of w. Then add δ(w) to the score of w.

Time is O(nm) with BFS and O(nm + n² log n) with Dijkstra; memory is O(n + m). Nodes are mapped to integer ids and adjacency is kept in plain Python lists, so on `airports` (500 nodes, 20,058 edges) it takes about 0.4 s in hop-count mode and about 1 s in weighted mode, far below the 30 s limit.

## Normalisation (same as NetworkX `betweenness_centrality`)
- **`normalized=true` (default):** raw scores are divided by (n−1)(n−2), the number of ordered pairs of nodes other than v, so scores lie in [0, 1]. For an undirected graph Brandes counts each pair twice (s→t and t→s), and the possible unordered pairs are (n−1)(n−2)/2. So the same divisor gives the correctly normalised value for undirected graphs too. With n ≤ 2 no node can lie between two others, so every score is 0.
- **`normalized=false`:** raw scores, with undirected scores halved so each unordered pair counts once. Directed scores are not changed.

## Directed and undirected graphs
- **Directed:** shortest paths follow edge direction (`out_neighbors`), and the pairs (s, t) and (t, s) are counted separately.
- **Undirected:** each edge can be used both ways, with the halving/normalisation above.
- **Weights:** by default paths are counted in hops and weights are ignored, which matches NetworkX's default (`weight=None`). With `weighted=true`, edge weights are used as path lengths. This makes sense for `airports` (weight = distance in km) but not for `lesmis`, where weight counts shared chapters (a strength, not a length). On an unweighted graph `weighted=true` changes nothing, and the summary notes this.
- Self-loops are ignored. Disconnected graphs are fine: pairs with no path between them contribute nothing.

## When to use it
- "Which airports are the most important transfer hubs?"
- "Which Les Misérables character connects otherwise separate groups?"
- "How central is Member 34 in the karate club?" (`node="m34"`)

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph or registered subgraph |
| top_k | integer | 10 | How many nodes to return (1 to 100) |
| normalized | boolean | true | Divide by (n−1)(n−2) (see above) |
| weighted | boolean | false | Use edge weights as path lengths instead of counting hops |
| node | string | none | Return only this node's score and rank |

## Output
A list of nodes, highest score first, with ties (equal after rounding to 6 decimal places) broken by node id in ascending order. `result_graph_id` is always `null`.

```json
[{"id": "FRA", "label": "Frankfurt am Main Airport", "score": 0.073318, "rank": 1},
 {"id": "AMS", "label": "Amsterdam Airport Schiphol", "score": 0.063791, "rank": 2}]
```

With `node`, the list holds just that node, with its `rank` among all nodes.

## Errors
- Unknown `graph_id`: suggests `list_graphs`.
- Unknown `node`: suggests `lookup_node`.
- `top_k` not a whole number from 1 to 100; `normalized` or `weighted` not true/false.
- Graph with no nodes.
- Negative edge weights with `weighted=true`: suggests `weighted=false`.
- Unknown extra parameters.

If every score is 0 (e.g. a graph made only of separate edges), the result is still `ok`, and the summary says that no node lies between two others.
