Strongly Connected Components

Student ID: fcd76f91
Difficulty: Medium
Category: Graph Algorithms
Output: Subgraph

1. Overview

Strongly connected components (SCCs) are groups of nodes in a directed graph where every node can reach every other node by following the direction of the edges.

For example, in a network of airports, an SCC represents a group of airports where it is possible to travel from any airport to any other airport within that group by following directed routes.

2. How It Works

I used Tarjan’s algorithm to find the strongly connected components. It identifies all components using a single depth-first search (DFS).

The algorithm uses two values for each node:

* index: The order in which the node is first visited.
* low: The smallest discovery index reachable from that node through the DFS traversal and applicable back edges.

The main steps are:

1. Visit each unvisited node using DFS and assign its index and low values.
2. Keep track of the active nodes using a stack and update the low values as the search progresses.
3. When a node’s low value equals its index, it is the root of an SCC.
4. Pop nodes from the stack until that root is reached. These nodes form one strongly connected component.

I implemented the DFS using an explicit stack instead of recursion. This avoids Python’s recursion limit when processing graphs with long paths.

Time complexity: O(V + E), excluding the additional cost of sorting neighbours, where V is the number of nodes and E is the number of edges.

3. Parameters

Parameter	    Type	      Default	      Description
graph_id	    string	    Required	    ID of the directed graph to analyse.
top_k	        integer	    10	          Number of largest components to return. Must be between 1 and 100.
node	        string	    None	  Optionally returns the strongly connected component containing the specified node.

4. Output

The result provides information about the components found in the graph.

Example:

{
  "num_components": 52,
  "largest_size": 74,
  "num_singletons": 5,
  "is_strongly_connected": false,
  "components": [
    {
      "rank": 1,
      "size": 74,
      "graph_id": "airports~2",
      "members": [
        {"id": "ABQ", "label": "Albuquerque International Sunport"}
      ],
      "members_truncated": true
    }
  ]
}

The output includes:

* num_components: Total number of strongly connected components.
* largest_size: Number of nodes in the largest component.
* num_singletons: Number of components containing only one node.
* is_strongly_connected: Whether the entire graph is strongly connected.
* components: The largest components, along with their sizes, members, and subgraph IDs.

Components are sorted by size in descending order. If two components have the same size, the component with the smaller first node ID comes first. Members within each component are sorted by node ID.

Each returned component is saved as a separate subgraph, and its ID is provided in graph_id.

The result_graph_id field identifies the largest component by default. If node is provided, it identifies the component containing that node instead. This ID can be used as input to another graph tool.

If node is provided, the output also includes a node_component entry describing its component.

To keep the response within the 8 KB limit, the number of members displayed per component may be reduced, followed by the number of components returned. The output summary indicates when this happens. The complete components remain available through their subgraphs.

5. Notes

* The algorithm supports directed graphs only.
* For undirected graphs, connected components should be used instead.
* Edge weights are ignored because the algorithm only considers edge directions and connectivity.
* A component containing one node is called a singleton. Such a component may also contain a self-loop.

6. Error Handling

The following cases return an error message:

* Unknown graph ID.
* Undirected graph supplied instead of a directed graph.
* top_k outside the range of 1–100.
* Requested node not found in the graph.
* Empty graph.
* Unsupported extra parameters.