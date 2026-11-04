# k_core

**Author:** 3f28ff34 · **Tier:** Medium · **Category:** Community

## What it computes
The **k-core** is the largest group of nodes where every node has at least `k`
connections inside the group. The tool finds it by "peeling": it keeps removing nodes
with fewer than `k` connections (removing one can push its neighbours below `k`, so they
are removed too) until no such node is left.
Doing this for k = 1, 2, 3, ... gives every node's **core number**: the largest k-core
it belongs to. The **densest core** is the core with the highest k.
Time complexity: O(V + E) for the peeling, plus one pass over the nodes per level.

## When to use it
For questions about the tightly connected centre of a network:
- "What is the tightly connected core of the karate club?"
- "Which airports are each linked to at least 30 others in the same group?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| k | integer | (none) | Minimum connections inside the core; 0 or more. **Leave it out to get the densest core.** |
| top_k | integer | 10 | How many core nodes to list (1 to 100) |

## Output
- `k`: the k used (when `k` is left out, this is the highest possible k).
- `max_core_number`: the k of the densest core.
- `size`: number of nodes in the k-core.
- `nodes`: up to `top_k` nodes of the core, each with `id`, `label` and `core_number`.
  Highest core number first, then by id.
- `result_graph_id`: the whole k-core as a subgraph. Other tools can run on it next.

Example: `graph_id=karate top_k=2`
```json
{"status": "ok",
 "result": {"k": 4, "max_core_number": 4, "size": 10,
            "nodes": [{"id": "m1", "label": "Member 1 (instructor)", "core_number": 4},
                      {"id": "m14", "label": "Member 14", "core_number": 4}]},
 "summary": "The 4-core of 'karate' has 10 nodes, each with at least 4 neighbours inside it; the densest core is the 4-core. The 2 with the highest core numbers are listed; the full core is in result_graph_id.",
 "result_graph_id": "karate~1", "error": null}
```

## Graphs it supports
- Undirected graphs: connections = neighbours.
- Directed graphs: connections = incoming + outgoing edges (same as NetworkX
  `core_number`). An edge in both directions (A→B and B→A) counts twice.
- Weights are ignored.

## Errors
| When | Message says |
| --- | --- |
| Unknown graph | No graph with that id; use `list_graphs` |
| Graph has no nodes | Nothing to compute |
| `k` is not a whole number of at least 0 (e.g. `-1`, `2.5`, `"2"`, `true`) | k must be a whole number of at least 0; leave k out for the densest core |
| `k` is larger than the densest core | There is no such core; gives the valid range 0 to max |
| `top_k` outside 1 to 100 | top_k must be a whole number from 1 to 100 |
| Unknown parameter | Lists the unknown parameter |

If the list would make the output larger than 8 KB, nodes are dropped from the end of the
list. `size` and the subgraph stay complete.
