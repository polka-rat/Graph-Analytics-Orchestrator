# topological_sort

**Author:** c1fb2ea9 · **Tier:** medium · **Category:** paths

## What it computes
Computes a linear topological ordering of nodes in a directed acyclic graph (DAG) such that for every directed edge $u \to v$, node $u$ appears before node $v$ in the sequence. If the graph contains any directed cycles, the algorithm identifies and returns the cycle, demonstrating why topological ordering is unfeasible. Ties among zero-in-degree nodes are broken deterministically by sorting node IDs in ascending lexicographical order.

**Time Complexity:** $\mathcal{O}(|V| + |E|)$ using Kahn's algorithm with a priority queue (min-heap) for degree tracking and DFS for cycle extraction when cycles exist.  
**Space Complexity:** $\mathcal{O}(|V|)$ auxiliary space for in-degree counts, min-heap, and the resulting sequence.

## When to use it
Use this tool for questions regarding dependency resolution, prerequisite planning, execution sequences, or detecting circular dependencies:
- *"In what order should these courses be taken?"*
- *"Can these tasks be completed in a valid sequence without dependency deadlocks?"*
- *"Does this dependency network contain any circular dependencies?"*

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| `graph_id` | string | (required) | ID of the graph to analyse (e.g. `"courses"`). |
| `top_k` | integer | null | (Optional) Limit the output sequence to the first $k$ nodes ($1 \le k \le 100$). |

## Output
Returns a structured dictionary conforming to the assignment tool contract:
- `status`: `"ok"` if the graph is a DAG, or `"error"` if the graph is undirected, missing, or contains a cycle.
- `result`: 
  - On success (DAG): An ordered list of node references `[{"id": "...", "label": "..."}, ...]` where each item is formatted with `node_ref(g, node)`.
  - On cycle detection: A list of node references forming the detected simple directed cycle.
- `summary`: A concise natural-language sentence detailing the topological order found or describing the detected cycle.
- `result_graph_id`: `null` (this tool does not register subgraphs).
- `error`: `null` on success, or a detailed error message describing what went wrong.

## Graphs it supports
- **Directed Acyclic Graphs (DAGs):** Fully supported (e.g. `"courses"`). Produces a valid linear ordering.
- **Cyclic Directed Graphs:** Detects the cycle, returns status `"error"`, and details the cycle in `error`, `summary`, and `result`.
- **Undirected Graphs:** Returns status `"error"` explaining that topological sorting requires a directed acyclic graph.

## Errors
- `Graph '<id>' does not exist`: Returned when an unknown `graph_id` is passed. Suggests using `list_graphs`.
- `Graph '<id>' is undirected`: Returned when an undirected graph is supplied. Explains that topological sorting requires a DAG.
- `Graph '<id>' is not a DAG; it contains a directed cycle`: Returned when cycles prevent topological sorting, specifying the cycle path.
- `Unknown parameter(s)`: Returned when unrecognised keyword arguments are supplied.
