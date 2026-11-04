# bipartite_matching

**Author:** 3f28ff34 · **Tier:** Hard · **Category:** Structure

## What it computes
A graph is **bipartite** if its nodes split into two groups (for example students and
projects) and every edge goes between the groups. A **matching** is a set of pairs joined
by an edge where no node is used twice. This tool finds a **maximum matching**: the most
pairs possible.

How it works:
1. **Find the two groups.** It uses the node attribute `side` if every node has one and
   every edge joins two different sides. Otherwise it colours the graph with BFS
   (2-colouring). If two neighbours get the same colour, the graph is not bipartite.
2. **Hopcroft-Karp.** Start with no pairs. In each round, a BFS finds the length of the
   shortest "augmenting path" (a path that starts and ends at unmatched nodes and
   alternates between unused and used edges). A DFS then finds such paths and flips them,
   which adds one pair each time. When no augmenting path is left, the matching is maximum.

Time complexity: O(E · √V). The DFS is iterative, so long paths cannot hit Python's
recursion limit.

## When to use it
For "assign each item to at most one partner" questions:
- "What is the best assignment of students to projects?"
- "How many students can each get a different project, and who is left out?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of a bipartite graph, e.g. `projects` |
| top_k | integer | 10 | Maximum entries in each list: pairs, unmatched left, unmatched right (1 to 100) |

## Output
- `left_side`, `right_side`: names of the two groups. The smaller group is the left side.
  Names come from the `side` attribute, or are `side A` / `side B`.
- `left_count`, `right_count`: number of nodes in each group.
- `matching_size`: number of pairs in the maximum matching.
- `pairs`: up to `top_k` pairs, each `{"left": node, "right": node}`, sorted by the left id.
- `unmatched_left`, `unmatched_right`: up to `top_k` nodes on each side with no partner.
- `result_graph_id` is always `null` (this tool does not create a subgraph).

Example: `graph_id=projects top_k=2`
```json
{"status": "ok",
 "result": {"left_side": "project", "right_side": "student", "left_count": 10, "right_count": 16,
            "matching_size": 9,
            "pairs": [{"left": {"id": "P01", "label": "Project 01"}, "right": {"id": "S05", "label": "Student 05"}},
                      {"left": {"id": "P02", "label": "Project 02"}, "right": {"id": "S02", "label": "Student 02"}}],
            "unmatched_left": [{"id": "P08", "label": "Project 08"}],
            "unmatched_right": [{"id": "S07", "label": "Student 07"}, {"id": "S08", "label": "Student 08"}]},
 "summary": "A maximum matching has 9 pairs between the 10 'project' nodes and the 16 'student' nodes; 1 'project' and 7 'student' nodes stay unmatched. Lists are cut to top_k entries; the counts above are complete.",
 "result_graph_id": null, "error": null}
```
P08 is unmatched because no student chose it.

**Note:** a graph can have more than one maximum matching. The size is always the same;
the exact pairs may differ from other tools (NetworkX itself returns different pairs
depending on which side it starts from). This tool always returns the same pairs for the
same input.

## Graphs it supports
- Any bipartite graph, connected or not, including isolated nodes. Unlike NetworkX
  `hopcroft_karp_matching`, it does not need to be told which nodes form one side, and
  it works on disconnected graphs such as `projects` without extra input.
- Directed graphs: edge direction is ignored, so an edge just means "these two can be
  paired". NetworkX's function expects an undirected graph; this tool treats a directed
  graph as its undirected version.
- Weights are ignored. It maximises the **number** of pairs, not their total weight.
- A graph with no edges gives `matching_size` 0 (not an error).

## Errors
| When | Message says |
| --- | --- |
| Graph is not bipartite (has an odd cycle or a self-loop) | Not bipartite, shows one edge on an odd cycle; suggests `projects` or `bipartite_check` |
| Unknown graph | No graph with that id; use `list_graphs` |
| Graph has no nodes | Nothing to match |
| `top_k` outside 1 to 100 | top_k must be a whole number from 1 to 100 |
| Unknown parameter | Lists the unknown parameter |

If the lists would make the output larger than 8 KB, entries are dropped from the longest
list. `matching_size` and the counts stay complete.
