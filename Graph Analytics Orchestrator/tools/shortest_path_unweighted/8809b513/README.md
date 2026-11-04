# shortest_path_unweighted

Finds a path with the fewest edges between two node IDs using breadth-first search. Edge weights are ignored. Directed graphs are traversed along outgoing edges; undirected graphs can be traversed in either direction. If several paths have the same minimum length, neighbors are visited in ascending node-ID order for deterministic output.

## Inputs

- `graph_id`: graph to search.
- `source`: starting node ID.
- `target`: destination node ID.

Use the provided `lookup_node` tool to find IDs from human-readable names.

## Output

On success, `result.path` is an ordered list of node references, each with an ID and label, and `result.hops` is the number of edges in the path. A source equal to the target returns that single node with zero hops. Unknown nodes, unknown graphs, and unreachable targets return a contract error.

## Algorithm

Breadth-first search explores nodes by increasing path length. Its running time is O(V + E) and its memory use is O(V), where V is the number of nodes and E the number of edges.

## Example

`python run_tool.py registry/tools/shortest_path_unweighted/8809b513 graph_id=airports source=MAA target=LIS`
