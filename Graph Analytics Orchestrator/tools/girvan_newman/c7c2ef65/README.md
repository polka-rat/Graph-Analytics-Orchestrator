# girvan_newman

**Author:** c7c2ef65 · **Tier:** hard · **Category:** community

## What it computes
Communities: groups of nodes more connected to each other than to the rest of the graph. The Girvan-Newman
method repeatedly removes the edge with the highest *edge betweenness*: the edge that the most shortest paths
cross, typically a bridge between groups. Each time the graph splits into one more piece, that is a new level
of the hierarchy. By default the tool returns the level with the highest modularity (how much denser the
groups are inside than chance would give). The unsplit graph counts as a level too, so a graph with no
community structure is reported as one group rather than force-split. `num_communities` asks for a fixed
number of groups instead.
Betweenness uses Brandes' algorithm. Worst-case time O(n·m²).

## Highlights
- **Same answer as NetworkX at every level, ties included.** When several edges have the same betweenness,
  the one removed decides the result. The adjacency is built in the same order NetworkX uses, and
  betweenness is summed in the same order, so equal scores compare equal and the same edge goes. Checked on
  every level of karate, lesmis, projects, courses and three airports subgraphs (352 levels, all identical).
- **4 to 6 times faster than NetworkX.** Removing an edge only changes betweenness inside that edge's own
  component, so only that component is recomputed; NetworkX recomputes the whole graph after every removal.

  | Graph | Nodes | Edges | This tool | NetworkX |
  | --- | --- | --- | --- | --- |
  | karate (default) | 34 | 78 | 0.03 s | |
  | lesmis (default) | 77 | 254 | 0.3 s | |
  | airports subgraph, full hierarchy | 110 | 433 | 0.3 s | 1.3 s |
  | airports subgraph, full hierarchy | 160 | 938 | 2.4 s | 8.4 s |

- **Never times out.** A work limit (n·m² ≤ 5·10⁸, about 200 nodes and 1,500 edges, around 7 s) returns a
  helpful error at once for larger graphs such as airports, instead of running past the 30 s limit.
- **Chains with other tools (↪).** Every listed community is registered as a subgraph, and its `graph_id`
  can go to any other tool; `result_graph_id` is the largest community.
- **Always under 8 KB.** If everything does not fit, member lists are shortened first, then fewer communities
  are listed; the summary says so, and the subgraphs still hold every member.
- **Useful order:** communities largest first; members most connected first, so the key people come first.

## When to use it
Questions about natural groups, and how a network breaks apart:
- "Into which two factions does the karate club split?" (`num_communities=2`)
- "What groups of characters appear together in Les Misérables?"
- "Which courses form separate tracks?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| num_communities | integer | best modularity | Number of communities, from 1 to the number of nodes |
| top_k | integer | 10 | How many of the largest communities to list (1 to 100) |

## Output
Example for `{"graph_id": "karate", "num_communities": 2}`. These are the two factions the club really split
into, with the instructor (m1) and the administrator (m34) on opposite sides:

```json
{"num_communities": 2, "modularity": 0.359961, "edges_removed": 11,
 "communities": [
   {"community": 1, "size": 19, "graph_id": "karate~1",
    "members": [{"id": "m34", "label": "Member 34 (administrator)"}, {"id": "m33", "label": "Member 33"}, "..."]},
   {"community": 2, "size": 15, "graph_id": "karate~2",
    "members": [{"id": "m1", "label": "Member 1 (instructor)"}, {"id": "m2", "label": "Member 2"}, "..."]}]}
```
Summary: *Girvan-Newman on 'karate': split into 2 communities as asked, modularity 0.359961, after removing
11 edges; the largest has 19 nodes.*

Communities are sorted by size (ties by smallest node id), and members by degree (ties by id). Modularity is
unweighted and rounded to 6 decimals. `result_graph_id` is the largest community's subgraph.

## Graphs it supports
Undirected and directed graphs; directed edges are treated as undirected, as in NetworkX. Weights are ignored.
Up to about 200 nodes and 1,500 edges: karate, lesmis, projects, courses, and filtered subgraphs of airports.
If the graph already has more separate components than `num_communities`, those components are returned
and the summary says so.

## Errors
Each returns `status: "error"` with a message saying how to fix the call:
- Unknown `graph_id`: use `list_graphs`.
- Graph too large: use louvain or label_propagation, or run on a smaller subgraph (e.g. from filter_nodes).
- `num_communities` not a whole number from 1 to the number of nodes.
- `top_k` outside 1 to 100, an unknown parameter, or a graph with no nodes.

## How it is tested
18 tests in `tests/`:
- every level matches `networkx` `girvan_newman` on karate, lesmis, projects and courses;
- the default equals the NetworkX level with the best modularity;
- a dense graph with no community structure is not split;
- the karate two-faction split;
- `result_graph_id` and node references;
- `top_k` and the 8 KB limit;
- the size limit, every error case and determinism.
