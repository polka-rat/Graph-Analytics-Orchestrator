# bipartite_matching (d02c8330)

**Answers:** "What is the best assignment of students to projects?", "How many students can get a project?", "Is a perfect matching possible?"

## Algorithm
1. **Sides.** If every node has `side_attribute` (default `side`) and it takes exactly two values,
   those values are the sides, and an edge inside one side is reported as an error. Otherwise the
   graph is 2-coloured by BFS, and an odd cycle is reported as an error ("not bipartite").
2. **Hopcroft–Karp**, O(E·√V). Each phase runs a BFS from all free left nodes to build distance
   layers. An iterative DFS (so deep paths cannot hit Python's recursion limit) then finds a maximal
   set of vertex-disjoint shortest augmenting paths. Dead-end nodes are pruned for the rest of the
   phase. Phases repeat until no augmenting path exists. Neighbours are visited in sorted order, so
   the output is deterministic.

## Parameters
| name | type | default | meaning |
|---|---|---|---|
| graph_id | string | required | bipartite graph, e.g. `projects` |
| side_attribute | string | `side` | node attribute holding the side |
| left_side | string | alphabetically first value | which side is "left" in the pairs |
| top_k | int | 10 | number of pairs and unmatched nodes to list (1–100) |

## Output
`matching_size`, `left_side`/`right_side` names, `left_size`, `right_size`, `perfect`, `pairs`
(`{left, right}` node refs, sorted by left id), `unmatched_left`, `unmatched_right`. When the list is
truncated, a `note` says to raise `top_k`.

## Edge cases
Non-bipartite graphs (odd cycle, self-loop, an edge inside one attribute side), an unknown `left_side`,
graphs with no edges between the sides, unknown graphs, bad `top_k` and unknown parameters all
return clear errors. Directed graphs are treated as undirected. Weights are ignored.

## Example
`python run_tool.py registry/tools/bipartite_matching/d02c8330 graph_id=projects left_side=student`
gives a maximum matching of 9: 7 students and 1 project stay unmatched.
