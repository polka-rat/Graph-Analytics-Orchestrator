Reachability

1. Overview

Reachability checks whether there is a path from one node to another in a graph. It helps determine whether two nodes are connected by following the edges.

For example, it can be used to check whether it is possible to travel from one airport to another through connecting flights.

2. How It Works

I used Breadth-First Search (BFS) to check whether the target node can be reached from the source node.

The algorithm works as follows:

1. Start the search from the source node and add it to a queue.
2. Visit neighbouring nodes and keep track of their parent nodes.
3. Continue until the target is found or there are no more nodes to visit.
4. If the target is found, use the parent information to reconstruct the path from the source to the target.

The neighbours are visited in sorted order to ensure that the same path is returned for the same input.

Since BFS explores nodes level by level, the returned path uses the minimum number of edges (hops).

Time complexity: O(V + E), excluding the additional cost of sorting neighbours, where V is the number of nodes and E is the number of edges.

3. Parameters

Parameter	  Type	      Default	      Description
graph_id	  string	    Required	    ID of the graph to search.
source	    string	    Required	    ID of the starting node. Can be found using lookup_node.
target	    string	    Required	    ID of the node to reach.
ignore_direction boolean	false	      If enabled, treats edges in a directed graph as bidirectional for the search.

4. Output

The result indicates whether the target is reachable and, if it is, provides a path between the source and target.

Example:

{
  "reachable": true,
  "source": {
    "id": "MAA",
    "label": "Chennai International Airport"
  },
  "target": {
    "id": "LIS",
    "label": "Humberto Delgado Airport (Lisbon Portela Airport)"
  },
  "hops": 2,
  "path": [
    {"id": "MAA", "...": "..."},
    {"id": "DXB", "...": "..."},
    {"id": "LIS", "...": "..."}
  ],
  "path_truncated": false,
  "directed": true
}

The output includes:

* reachable: Whether the target can be reached.
* hops: Number of edges in the returned path.
* path: Nodes along the path from source to target.
* path_truncated: Indicates whether the path has been shortened in the response.
* directed: Indicates whether the original graph is directed.

If no path exists, reachable is false, hops is null, and path is empty. In this case, nodes_reachable_from_source gives the number of nodes reachable from the source.

If a path contains more than 40 nodes, only the first 20 and last 20 nodes are returned, and path_truncated is set to true.

The algorithm does not create a separate subgraph.

5. Notes

* Supports directed and undirected graphs, including subgraphs created by other tools.
* Edge weights are ignored because reachability depends only on the presence of edges.
* In a directed graph, reaching node B from node A does not necessarily mean A can be reached from B.
* Setting ignore_direction=true allows traversal in either direction along an edge.
* A node is always reachable from itself, with zero hops.

6. Error Handling

The following cases return an error message instead of causing the program to crash:

* Unknown graph ID.
* Missing source or target.
* Source or target node not found in the graph.
* Invalid value for ignore_direction.
* Unsupported extra parameters.