# Strongly Connected Components

**Tool:** strongly_connected_components  
**Student ID:** 80ae2fd8  
**Algorithm:** Kosaraju's algorithm

## Purpose

This tool identifies the strongly connected components (SCCs) of a directed graph. A strongly connected component is a maximal set of nodes in which every node can reach every other node by following directed edges.

## Algorithm

Kosaraju's algorithm uses two depth-first-search passes:

1. Traverse outgoing edges and record nodes in finishing order.
2. Process nodes in reverse finishing order, traversing incoming edges.
3. Collect each traversal as a strongly connected component.
4. Sort nodes and components deterministically by node ID.

The implementation uses iterative depth-first searches to avoid recursion-depth limitations.

## Input

- `graph_id` (string): ID of the directed graph to analyse.

The tool returns an error if the graph does not exist or is undirected.

## Output

The result includes the graph ID, number of components, and a list of components. Each component contains its ID, size, and node references.

## Complexity

Time complexity: O(V + E). Additional space complexity: O(V), where V is the number of nodes and E is the number of edges.

## Example

`python run_tool.py registry/tools/strongly_connected_components/80ae2fd8 graph_id=airports`

## Tests

The unit tests cover directed cycles, one-way chains, multiple components connected by a one-way edge, isolated nodes, undirected-graph errors, and unknown graph IDs.
