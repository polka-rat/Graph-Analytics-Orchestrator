# betweenness_centrality

**Author:** c1fb2ea9 · **Tier:** hard · **Category:** centrality

## What it computes
Computes betweenness centrality for every node in a graph using Brandes' algorithm (2001). Betweenness centrality measures the extent to which a node lies on the shortest paths between all other pairs of nodes:
$$C_B(v) = \sum_{s \neq v \neq t} \frac{\sigma_{st}(v)}{\sigma_{st}}$$
where $\sigma_{st}$ is the total number of shortest paths from node $s$ to node $t$, and $\sigma_{st}(v)$ is the number of those paths passing through $v$. Results are optionally normalized by the number of possible node pairs: $\frac{2}{(n-1)(n-2)}$ for undirected graphs and $\frac{1}{(n-1)(n-2)}$ for directed graphs ($n = |V|$). Nodes are sorted descending by score, breaking ties deterministically by node ID in ascending lexicographical order.

**Time Complexity:** $\mathcal{O}(|V| \cdot (|V| + |E|))$ using BFS for shortest-path counting and backward dependency accumulation. On `airports` (500 nodes, 20,058 edges), it executes in under 2 seconds.  
**Space Complexity:** $\mathcal{O}(|V| + |E|)$ auxiliary space for BFS predecessors, distance maps, and dependency values.

## When to use it
Use this tool to find bottleneck nodes, brokers, critical communication bridges, or critical transfer hubs:
- *"Who are the key brokers between groups?"*
- *"Which airports serve as the most critical transfer hubs connecting other routes?"*
- *"Which character in Les Misérables connects otherwise isolated communities?"*

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| `graph_id` | string | (required) | ID of the graph to analyse (e.g. `"karate"`, `"airports"`, `"lesmis"`). |
| `top_k` | integer | 10 | Number of top nodes to return (1 to 100). |
| `normalized` | boolean | true | Whether to normalize scores by $\frac{2}{(n-1)(n-2)}$ (undirected) or $\frac{1}{(n-1)(n-2)}$ (directed). |

## Output
Returns a structured dictionary conforming to the assignment tool contract:
- `status`: `"ok"` or `"error"`.
- `result`: A list of top-$k$ node reference dictionaries `[{"id": "...", "label": "...", "score": 0.437635}, ...]` where scores are rounded to 6 decimal places.
- `summary`: A concise natural-language sentence identifying the highest-ranked node and its score.
- `result_graph_id`: `null` (this tool does not generate subgraphs).
- `error`: `null` on success, or an error message on failure.

## Graphs it supports
- **Undirected graphs:** Fully supported (e.g. `"karate"`, `"lesmis"`, `"projects"`). Automatically divides symmetric pair paths by 2.
- **Directed graphs:** Fully supported (e.g. `"courses"`, `"airports"`). Evaluates directed shortest paths and uses directed pair normalization.
- **Weighted & unweighted graphs:** Evaluates structural shortest paths (hop counts) using standard unweighted BFS.

## Errors
- Unknown `graph_id`: Returns a structured error indicating that the graph was not found and suggesting `list_graphs`.
- Invalid `top_k`: Returns a structured error if `top_k` is not an integer between 1 and 100.
- Invalid `normalized`: Returns a structured error if `normalized` is not a boolean.
- Unknown parameter(s): Returns a structured error listing unknown arguments.
