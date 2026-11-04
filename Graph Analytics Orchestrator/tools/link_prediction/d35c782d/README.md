# link_prediction

**Author:** d35c782d · **Tier:** medium · **Category:** structure

## What it computes
Ranks pairs of nodes that are not linked yet by how likely they are to become linked, using the neighbours they share. Every unlinked pair is scored with the chosen method and the best `top_k` are returned, highest score first, with ties broken by node id (ascending) and scores rounded to 6 decimals. Time complexity is O(n² · d) to rank all pairs (n nodes, typical neighbour-set size d) and O(n · d) when a `node` is given.

Methods (N(x) are the neighbours of x, deg(x) is its number of links):
- `adamic_adar` (default): sum of 1 / log deg(w) over the shared neighbours w. Rare shared neighbours count more, so it suits friend and social networks.
- `common_neighbors`: number of shared neighbours. A simple baseline.
- `jaccard`: shared neighbours divided by all neighbours of the two nodes. It reduces the advantage of well-connected nodes.
- `resource_allocation`: sum of 1 / deg(w) over the shared neighbours. Penalises hubs more strongly, so it suits sparse networks with hubs.
- `preferential_attachment`: deg(u) × deg(v). Suits hub networks such as `airports`, where new links tend to go to big hubs.
- `community_resource_allocation`: resource allocation that counts only shared neighbours in the same community as the pair, and scores 0 for pairs in different communities (Soundarajan–Hopcroft). Needs `community_attribute`, e.g. `club` on `karate` or `country` on `airports`.

## When to use it
Use it to suggest new links.
- "Who should Alice connect with next?" (give `node`)
- "Which new routes are most likely in the airport network?" (no `node`, e.g. `preferential_attachment`)

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| node | string | none | Node id. If given, returns the best new partners for this node; if omitted, returns the best pairs in the whole graph |
| method | string | adamic_adar | One of the six methods above |
| community_attribute | string | none | Node attribute that groups nodes into communities; required for `community_resource_allocation` |
| use_direction | boolean | false | Directed graphs only. false ignores link direction; true follows it (see below). Ignored on undirected graphs |
| top_k | integer | 10 | How many results to return (1 to 100) |

## Output
`result` is a list, highest score first.
- With `node`: each entry is the partner node `{id, label, score}`.
- Without `node`: each entry is `{source: {id, label}, target: {id, label}, score}`. On undirected graphs the pair is ordered by id; with `use_direction` the pair is source → target.

The list is shortened if the output would pass 8 KB, and the summary says how many pairs were scored. The tool does not return `result_graph_id` (it is null).

Example (`graph_id=karate top_k=2`):
```json
{"status": "ok",
 "result": [{"source": {"id": "m3", "label": "Member 3"}, "target": {"id": "m34", "label": "Member 34 (administrator)"}, "score": 4.719381},
            {"source": {"id": "m1", "label": "Member 1 (instructor)"}, "target": {"id": "m34", "label": "Member 34 (administrator)"}, "score": 2.71102}],
 "summary": "Most likely new link by adamic_adar: Member 3 - Member 34 (administrator), score 4.719381. Showing 2 of 483 unlinked pairs scored. Edge weights are ignored.",
 "result_graph_id": null, "error": null}
```

## Graphs it supports
Undirected and directed graphs. Edge weights are ignored (the summary says so), because weights mean different things in different graphs, e.g. strength in `lesmis` but kilometres in `airports`.

On directed graphs the default (`use_direction=false`) treats links as undirected. With `use_direction=true` a pair u → v is scored from u's outgoing links and v's incoming links: shared neighbours are the nodes u points to that also point to v, the preferential-attachment degrees are out-degree(u) × in-degree(v), and a node's degree counts its incoming plus outgoing links. Only pairs with no link u → v are candidates, and with `node` the candidates are new links from that node.

Ranking all pairs is refused for graphs with more than 2,000 nodes; give a `node` instead.

## Errors
- Unknown `graph_id`: no such graph (use `list_graphs`).
- Unknown parameter name.
- `top_k` is not a whole number from 1 to 100.
- `method` is not one of the six methods.
- `use_direction` is not true/false.
- `node` is not a node of the graph (use `lookup_node`).
- All-pairs ranking requested on a graph with more than 2,000 nodes.
- `community_resource_allocation` without a valid `community_attribute`; the error lists the attributes the graph has (or says there are none).

