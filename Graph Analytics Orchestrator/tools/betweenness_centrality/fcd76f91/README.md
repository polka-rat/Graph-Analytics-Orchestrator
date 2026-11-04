Betweenness Centrality

1. Overview

Betweenness centrality is a graph algorithm used to identify important nodes that connect different parts of a network. It measures how often a node appears on the shortest paths between other pairs of nodes.

For example, in an airport network, an airport with a high betweenness centrality score may act as an important connection between different cities.

2. Algorithm

I implemented Brandes’ algorithm to calculate betweenness centrality. It avoids calculating the shortest paths separately for every pair of nodes, making the computation more efficient.

For each source node, the algorithm follows these steps:

1. Find shortest paths: Use BFS for unweighted graphs and Dijkstra’s algorithm for weighted graphs.
2. Count shortest paths: Store the number of shortest paths to each node in sigma[v] and keep track of its predecessor nodes.
3. Calculate dependencies: Process the nodes in reverse order and calculate how much each node contributes to the scores of its predecessors.
    The dependency calculation uses the following formula:
    delta[v] += sigma[v] / sigma[w] * (1 + delta[w])
4. Calculate final scores: Add the dependency values to the corresponding betweenness centrality scores.

After processing every source node, the algorithm returns the nodes with the highest scores.

3. Time Complexity

Let V be the number of nodes and E be the number of edges.

* Unweighted graphs: O(V × E)
* Weighted graphs: O(V × E + V² log V), assuming Dijkstra’s algorithm uses a binary heap.

To improve performance, I convert the graph into lists indexed by node numbers before running the main algorithm. This reduces the overhead of accessing graph data.

I tested the implementation against NetworkX’s betweenness centrality results on all five datasets.

4. Parameters

Parameter	    Type	      Default    	  Description
graph_id	    string	    Required	    ID of the graph to analyse.
top_k	        integer	    10	          Number of top nodes to return. Must be between 1 and 100.
node	       string	   None	   Returns the score and rank of a specific node, even if it is outside the top results
weighted	    boolean   	false       	Uses edge weights as distances when finding shortest paths.
normalized	  boolean	    true	        Determines whether the scores are normalized.

5. Output Format

The algorithm returns a list of nodes sorted by their betweenness centrality scores in descending order.

Example:

[
  {
    "id": "m1",
    "label": "Member 1 (instructor)",
    "score": 0.437635,
    "rank": 1
  },
  {
    "id": "m34",
    "label": "Member 34 (administrator)",
    "score": 0.304075,
    "rank": 2
  }
]

The output follows these rules:

* Scores are rounded to six decimal places.
* If two nodes have the same score, they are ordered by node ID.
* If the requested node is not in the top top_k results, its score and actual rank are added at the end.
* If the response exceeds the 8 KB size limit, entries are removed from the bottom until the response fits. The summary indicates how many entries are returned.
* The algorithm calculates the scores directly without creating a separate subgraph.

6. Normalization

The normalized parameter controls how the scores are scaled.

* normalized=true: Scores are normalized so that they can be compared across graphs of different sizes.
* normalized=false: Raw betweenness centrality scores are returned. For undirected graphs, the scores are divided by two because each pair is counted from both directions.

The normalization follows the convention used by NetworkX’s betweenness_centrality function.

7. Supported Graphs

The implementation supports:

* Directed and undirected graphs.
* Weighted and unweighted graphs.
* Disconnected graphs.

For directed graphs, shortest paths follow the direction of the edges. If no path exists between two nodes, that pair does not contribute to the scores.

When weighted=true is used on a graph without edge weights, the algorithm falls back to BFS because all edges are treated equally.

8. Error Handling

The implementation handles the following cases:

Error	Description
Unknown graph	The given graph ID does not exist.
Invalid top_k	The value is outside the range of 1–100.
Unknown node	The requested node is not present in the graph.
Invalid boolean value	weighted or normalized is not set to true or false.
Negative edge weights	Negative weights are rejected when weighted=true.
Empty graph	The graph contains no nodes.
Unknown parameters	Unsupported extra parameters are rejected.