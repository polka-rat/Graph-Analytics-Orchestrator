# degree_distribution

**Author:** c1fb2ea9 · **Tier:** easy · **Category:** structure

## What it computes
Computes the degree distribution (histogram of node degrees) across all nodes in the given graph. The result is a list where each index $k$ represents the degree and the value at that index is the count of nodes having degree $k$, exactly matching `networkx.degree_histogram(G)`. For directed graphs, the degree is the total degree (in-degree plus out-degree), following standard NetworkX semantics.

**Time Complexity:** $O(V + E)$ where $V$ is the number of nodes and $E$ is the number of edges, as each node and its incident edges are inspected once to compute degrees, followed by an $O(V + \Delta)$ pass to bin counts into a histogram of size $\Delta + 1$ (where $\Delta$ is maximum degree).  
**Space Complexity:** $O(V + \Delta)$ auxiliary space to store node degrees and the resulting histogram.

## When to use it
Use this tool for questions about network structure, connection density patterns, and degree frequency:
- *"Do most nodes have only a few connections?"*
- *"What is the most frequent node degree in the network?"*
- *"What is the maximum degree in the graph, and how many nodes have it?"*

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| `graph_id` | string | (required) | ID of the graph to analyse (e.g. `"karate"`, `"airports"`, `"lesmis"`). |

## Output
Returns a structured dictionary conforming to the assignment tool contract:
- `status`: `"ok"` or `"error"`.
- `result`: A list of integer counts where index $i$ corresponds to degree $i$ (e.g. `[0, 1, 11, 6, 6, 3, 2, ...]`). It also supports dictionary-style key access (e.g., `["histogram"]`, `["max_degree"]`, `["min_degree"]`, `["mean_degree"]`, `["mode_degree"]`, `["total_nodes"]`).
- `summary`: A concise natural-language sentence describing the graph, total nodes, degree range, mean degree, and mode degree.
- `result_graph_id`: `null` (this tool does not generate subgraphs).
- `error`: `null` on success, or an error message on failure.

## Graphs it supports
- **Undirected graphs:** Calculates standard degree for each node.
- **Directed graphs:** Calculates total degree (sum of in-degree and out-degree) for each node, conforming to NetworkX `G.degree()` and `nx.degree_histogram(G)`.
- **Weighted & unweighted graphs:** Evaluates structural connectivity (edge counts), ignoring edge weight magnitudes.

## Errors
- Unknown `graph_id`: Returns a structured error indicating that the graph was not found and recommending `list_graphs`.
- Unexpected parameters: Returns a structured error listing unknown parameters and stating that only `graph_id` is accepted.
