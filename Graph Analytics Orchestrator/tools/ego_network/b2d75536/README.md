# ego_network

**Author:** b2d75536 · **Tier:** easy · **Category:** subgraph

## What it computes
The ego network of a node: the node itself (the *ego*), every node within `radius`
steps of it (the *alters*), and all edges among that set. A breadth-first search
from the centre collects the nodes, and `store.subgraph` registers the induced
subgraph, which keeps every edge among the members, not only the ones touching the
centre. The search visits each node and edge once, so it runs in O(V + E); ranking
the members costs a further O(V log V).

## When to use it
For questions about the local neighbourhood of one node, and how its neighbours
relate to each other:

- "Show me Member 1's immediate network in the karate club."
- "Which airports are one hop from Chennai, and how well connected are they to each other?"

For the node *set* within k steps, `k_hop_neighborhood` is the better fit. This tool
is about the subgraph and how dense it is.

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| node | string | (required) | Id of the centre node |
| radius | integer | 1 | Steps out from the centre, 1 to 5 |
| direction | string | "both" | On a directed graph: "both", "out" or "in" |
| include_center | boolean | true | Whether the centre is part of the network |
| top_k | integer | 10 | How many members to list (1 to 100) |

## Output
`result` holds the centre, the settings used, and the shape of the network:

```json
{"center": {"id": "m1", "label": "Member 1 (instructor)"},
 "radius": 1, "direction": "both", "include_center": true,
 "alters": 16, "nodes": 17, "edges": 34, "density": 0.25,
 "members_shown": 10,
 "members": [{"id": "m2", "label": "Member 2", "links_inside": 8, "steps_from_center": 1}],
 "graph_id": "karate~1"}
```

`members` lists the alters, best connected first, where `links_inside` counts how
many other members a node is joined to (direction ignored) and `steps_from_center`
is its distance from the ego. `density` is the share of possible edges that are
present. The whole network is registered as a graph and its id is returned in
`result_graph_id`, so another tool can run on it. If a long listing would push the
response past the 8 KB limit, the least connected members are dropped and
`members_shown` says how many are left.

## Graphs it supports
All of them: directed and undirected, weighted and unweighted. Weights are carried
into the registered subgraph but do not affect which nodes are selected. On an
undirected graph `direction` is ignored and reported back as `"both"`.

## Errors
| When | Message |
| --- | --- |
| Unknown `graph_id` | No graph with that id; use `list_graphs` |
| Unknown or missing `node` | Node not in the graph; use `lookup_node` to find ids |
| `radius` not a whole number from 1 to 5 | Says the allowed range |
| `direction` not "both", "out" or "in" | Lists the three values |
| `include_center` not true or false | Says it must be a boolean |
| `top_k` outside 1 to 100 | Says the allowed range |
| Any other parameter | Lists the parameters the tool takes |
| `include_center=false` for a node with no neighbours | The network would be empty; suggests `include_center=true` or a larger radius |
