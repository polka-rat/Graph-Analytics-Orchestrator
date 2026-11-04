# TODO_tool_name

**Author:** YOUR_ID · **Tier:** TODO · **Category:** TODO

## What it computes
TODO: the algorithm, in two or three sentences, and its time complexity.

## When to use it
TODO: the kinds of questions it answers, with two example questions.

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| top_k | integer | 10 | How many results to return (1 to 100) |

## Output
TODO: what `result` contains, with a short example. Whether it returns `result_graph_id`.

## Graphs it supports
TODO: directed and/or undirected; weighted and/or unweighted; what happens otherwise.

## Errors
TODO: each error the tool can return and why.





# Reachability

## Description
Checks whether a target node can be reached from a source node.

## Algorithm
Uses depth-first search (DFS). It tracks visited nodes to avoid revisiting them. For directed graphs, it follows outgoing edges. For undirected graphs, it follows undirected neighbours.

## Complexity
Time: O(V + E)
Space: O(V)

## Example
Graph: karate
Source: m1
Target: m2

The tool returns whether the target is reachable from the source.