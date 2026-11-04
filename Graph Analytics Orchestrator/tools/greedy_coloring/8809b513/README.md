# greedy_coloring

Assigns colors to graph nodes with a deterministic greedy algorithm. Nodes are processed in descending order of degree; ties are broken by ascending node ID. Each node receives the smallest positive color not used by its already-colored neighbors.

For directed graphs, an edge in either direction makes its endpoints conflict. Edge weights are ignored. The result gives whole-graph color statistics and up to `top_k` node assignments, ordered by node ID, to keep the response bounded.

## Inputs

- `graph_id`: graph to color.
- `top_k`: maximum number of node assignments to return (default 10, maximum 100).

## Output

- `color_count`: number of colors used for the complete graph.
- `color_class_sizes`: number of nodes assigned each color, where list position 1 corresponds to color 1.
- `total_nodes`: number of nodes colored.
- `assignments`: returned node references, each with an ID, label, and color.

An empty graph or a graph containing a self-loop returns a helpful error. The algorithm runs in O(V + E + V log V) time plus neighbor color checks, and uses O(V + E) memory.

## Example

`python run_tool.py registry/tools/greedy_coloring/8809b513 graph_id=karate top_k=10`
