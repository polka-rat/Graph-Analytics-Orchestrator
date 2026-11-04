# bipartite_matching

**Author:** 8809b513 · **Tier:** hard · **Category:** structure

## What it computes

Computes a maximum-cardinality matching: a set of edges in which no node is used more than once. Hopcroft–Karp repeatedly finds shortest augmenting paths in phases and runs in O(E√V) time for a bipartite graph.

## When to use it

Use this tool for assignment and pairing questions where connections mean eligibility, such as “What is the largest set of students that can each be assigned a different project?” or “How many people can be paired with distinct available roles?”

## Parameters

| Name | Type | Meaning |
| --- | --- | --- |
| graph_id | string | ID of the graph to match; for the supplied student/project example, use `projects`. |

## Output

`result.matching_size` is the number of assignments. `result.matching` contains disjoint pairs of node references. For the provided `projects` graph, each pair has `student` and `project` fields, and unmatched students/projects are returned separately. For other bipartite graphs, pairs and unmatched nodes use `left` and `right` fields. The tool does not register a result graph.

## Graphs it supports

Undirected, unweighted or weighted bipartite graphs; edge weights are ignored. Directed graphs are rejected because eligibility is represented by undirected edges. If node `side` attributes consistently identify `student` and `project`, those names define the sides. Otherwise, the tool determines a bipartition using breadth-first search. A self-loop or odd cycle returns an error.

## Errors

Returns a contract error for an unknown graph, unknown parameters, a directed graph, or a graph that is not bipartite. Use `list_graphs` to find graph IDs and provide an undirected graph with two groups and cross-group edges.

## Example

`python run_tool.py registry/tools/bipartite_matching/8809b513 graph_id=projects`
