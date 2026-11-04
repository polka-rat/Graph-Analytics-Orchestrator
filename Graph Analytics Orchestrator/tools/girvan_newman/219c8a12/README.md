# girvan_newman ↪

**Author:** 219c8a12 · **Tier:** hard · **Category:** community · **Registers subgraphs:** yes

## What it computes
The Girvan–Newman method finds communities by **repeatedly removing the edge with the highest betweenness**: the edge that the most shortest paths cross, which is typically a bridge between groups. As the bridges disappear the graph falls apart into components, and each component is a community. Every time the number of components grows, the partition is recorded together with its **modularity** on the original graph:

Q = Σ_c [ L_c / m − (d_c / 2m)² ]

where L_c is the (weighted) number of edges inside community c, d_c is the sum of the degrees in c, and m is the total edge weight.

**Algorithm.**
1. **Edge betweenness (Brandes, edge variant).** From every source, run a BFS that counts the shortest paths σ. Then walk the BFS order backwards, pushing the dependency σ_v/σ_w·(1 + δ_w) onto each edge (v, w) of the shortest-path DAG. Cost O(n·m) per pass.
2. **Remove the top edge.** Ties are broken exactly as NetworkX breaks them: the first maximal edge in NetworkX's `G.edges()` order.
3. **Recompute only the changed component(s).** Edges in other components keep their values; Brandes' sum for them is unchanged, number for number.
4. **Record each split** with its modularity.
5. **Stop** when `num_communities` is reached. Otherwise continue until no edges are left, then return the split with the highest modularity (on ties, the one with fewer communities).

**Reproducibility.** The adjacency order, BFS order, floating-point summation order and tie-breaking all replicate `nx.community.girvan_newman`. I checked this against NetworkX 3.7 at **every level** of the dendrogram on karate (33 levels), lesmis (76), projects (24) and courses (20): all 153 partitions are identical.

**Cost.** Naïve Girvan–Newman is O(m²·n). The component-local recompute makes it much cheaper once the graph has split. Runtimes: karate takes under 0.02 s and the full lesmis dendrogram about 0.2 s. On `airports` (10,126 undirected edges) one betweenness pass takes about 0.9 s, so the tool stops at its fixed work limit (about 11 passes, roughly 10 s) and says so (see below).

## When to use it
- "How does the karate club break apart into groups?" → `{"graph_id": "karate"}`
- "Split the club into its two factions" → `{"graph_id": "karate", "num_communities": 2}`
- Follow-up analysis on one group: pass the returned `result_graph_id` to another tool (e.g. `clustering_coefficient`).

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph (a dataset or a registered subgraph) |
| num_communities | integer | none | Stop when the graph has this many communities (1 to n). If omitted, return the highest-modularity split |
| max_removals | integer | 1000 | Safety cap on edge removals (1 to 100,000) |
| top_k | integer | 10 | How many communities to list, largest first (1 to 100) |
| community_index | integer | 0 | Which community becomes `result_graph_id` (0 = largest) |
| weighted | boolean | true | Modularity uses edge weights (as `nx.community.modularity` does by default). Edge removal never uses weights |
| max_seconds | number | 20 | Backstop time limit (at most 25 s) for very slow machines; normally the fixed work limit stops large runs first. The best split found so far is returned |

## Output
`result` is an object with these fields:
- `num_communities`, `modularity` (6 dp) and `edges_removed` for the chosen split.
- `communities`: the largest first (ties broken by smallest node id), at most `top_k`. Each is `{"community": i, "size": s, "graph_id": "<registered subgraph id>", "sample_nodes": [{"id", "label"}, ...]}`. The sample lists up to 10 members (never more than `top_k`), best-connected first (by degree in the original graph, ignoring direction; equal degrees by ascending node id). To get **all** members, call any tool on that entry's `graph_id`.
- `splits`: the modularity of each recorded split, as `{"communities", "modularity", "edges_removed"}`, so you can see how the network falls apart. At most `top_k` splits are listed (the first ones, up to 25), and the chosen split is always included.

**Registered subgraphs.** The `top_k` largest communities (plus `community_index`, if it falls outside them) are registered with `store.subgraph`. `result_graph_id` is the `community_index` community, the largest by default. Registration happens *before* the size check: if the response would pass the 7,500-byte target (safely under the 8 KB limit), the sample size and then the number of listed communities shrink, and the summary says so. The communities left out of the listing stay registered (ids `<graph>~1`, `~2`, … in community order), but their ids don't appear in the response.

```json
{"status": "ok",
 "result": {"num_communities": 5, "modularity": 0.401298, "edges_removed": 24,
            "communities": [{"community": 0, "size": 12, "graph_id": "karate~1",
                             "sample_nodes": [{"id": "m34", "label": "Member 34 (administrator)"}, "..."]}, "..."],
            "splits": [{"communities": 1, "modularity": 0.0, "edges_removed": 0}, "..."]},
 "summary": "Girvan-Newman splits 'karate' into 5 communities by removing 24 edges (modularity 0.401298, the highest of the 34 splits explored); the largest has 12 of 34 nodes. Community 0 is registered as subgraph 'karate~1' (result_graph_id); 'splits' shows the first 25 of 34 splits.",
 "result_graph_id": "karate~1", "error": null}
```

## Graphs it supports
- **Undirected:** the natural case.
- **Directed:** treated as undirected (as `nx.community.girvan_newman` does), and the summary says so.
- **Weighted:** edge betweenness uses hop counts (standard, unweighted Girvan–Newman). By default modularity includes the weights. The summary states both.
- **Already disconnected:** the existing components are the starting partition. If `num_communities` is at most the current number of components, those components are returned without removing any edge. Unlike `nx.community.girvan_newman`, the starting partition is also a candidate for the best-modularity split.
- **Self-loops** are ignored.
- **Large graphs:** the run is bounded by a fixed work limit of 120 million node and edge visits (one betweenness pass over a component costs |C|·(|C| + 2|E_C|)), checked *before* each pass. Because it counts work rather than seconds, the output is the same on every machine. `max_seconds` (default 20 s) is only a backstop for very slow machines, and `max_removals` caps the number of removals. If a limit is reached, the best split found so far is returned with a note. If no split was found at all (e.g. `airports`), the summary opens by saying so and why (too slow for that graph, or the `max_removals` cap), and suggests narrowing it with `filter_nodes` or using a faster community tool (or raising `max_removals`). The small datasets never come near the work limit (the full lesmis dendrogram uses about 1 % of it).

## Errors
| Situation | Response |
| --- | --- |
| Unknown `graph_id` | error, suggesting `list_graphs` |
| Graph with no edges | error: nothing to split |
| `num_communities` < 1 or > number of nodes | error giving the valid range |
| `community_index` ≥ number of communities in the chosen split | error giving the valid range |
| `top_k`, `max_removals`, `max_seconds` out of range; non-boolean `weighted` | error giving the valid values |
| Unknown parameter | error listing the accepted parameters |
| work limit, `max_removals` or `max_seconds` reached | `ok`, best split so far, explained in the summary |
