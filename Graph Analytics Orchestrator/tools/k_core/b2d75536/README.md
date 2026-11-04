# k_core

**Author:** b2d75536 · **Tier:** medium · **Category:** community

## What it computes
The *k-core* is the largest subgraph in which every node has at least k neighbours
inside the subgraph; a node's *core number* is the largest k whose core still
contains it. Both come out of one peeling pass: take the node with the smallest
current degree, record the largest degree seen so far as its core number, remove it,
and lower the degree of its remaining neighbours. A binary heap holds the current
degrees, with stale entries skipped, so the pass costs O(E log V) and is what
Batagelj and Zaversnik describe (their bucket version is O(V + E); the heap is used
here because it is short and clearly correct). The chosen core is then the set of
nodes whose core number is at least k, registered as a subgraph.

Degree here counts neighbours, not weight. On a directed graph a node's degree is
its in-degree plus its out-degree, the usual convention and the one NetworkX uses,
so a pair joined in both directions counts twice. Self-loops are ignored, since a
node cannot hold itself in a core.

## When to use it
For questions about the dense heart of a network, or how deep a node sits in it:

- "What is the tightly connected core of the airport network?"
- "Which characters remain if everyone with fewer than four co-appearances is removed, over and over?"

Unlike `connected_components`, which asks whether nodes are joined at all, this asks
how *redundantly* they are joined.

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| k | integer | (the densest core) | Which core to return; every member has at least k links to other members |
| top_k | integer | 10 | How many members to list (1 to 100) |

## Output
```json
{"k": 4, "max_core": 4, "core_size": 10, "core_edges": 25,
 "core_distribution": [{"k": 1, "nodes": 1}, {"k": 2, "nodes": 11},
                       {"k": 3, "nodes": 12}, {"k": 4, "nodes": 10}],
 "members_shown": 10,
 "members": [{"id": "m1", "label": "Member 1 (instructor)", "core_number": 4, "links_inside": 9}],
 "graph_id": "karate~1"}
```

`max_core` is the highest core number in the graph, `core_distribution` says how
many nodes have each core number, and `members` lists the core, highest core number
first and then by id. `links_inside` counts a member's neighbours within the core.
The core is registered as a graph whose id is returned in `result_graph_id`. If the
response would pass 8 KB, the listing is shortened first and the distribution after
it, and `members_shown` says how many members are left.

## Graphs it supports
All of them: directed and undirected, weighted and unweighted. Weights are ignored,
because the k-core is defined by how *many* neighbours a node has.

## Errors
| When | Message |
| --- | --- |
| Unknown `graph_id` | No graph with that id; use `list_graphs` |
| `k` negative, or not a whole number | Says k must be 0 or more, or left out |
| `top_k` outside 1 to 100 | Says the allowed range |
| Any other parameter | Lists the parameters the tool takes |
| Graph with no nodes | Says the graph has no cores |

Asking for a `k` above `max_core` is not an error: the answer is a real one, an
empty core. The tool returns `status: "ok"` with `core_size` 0, no
`result_graph_id`, and a summary naming the densest core that does exist.
