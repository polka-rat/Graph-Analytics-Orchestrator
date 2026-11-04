# degree_distribution

**Author:** c7c2ef65 · **Tier:** easy · **Category:** structure

## What it computes
The degree of every node, then how many nodes have each degree, plus the minimum, maximum and mean degree.
This shows the shape of a network at a glance: are connections spread evenly, or held by a few hubs?
Edge weights are ignored. Time O(V + E).

## Highlights
- **Fast:** one pass over the adjacency lists; airports (500 nodes, 20,058 edges) takes under 0.1 s.
- **Matches NetworkX:** with the default `mode="total"`, the counts are `nx.degree_histogram(G)`, tested on all
  five datasets.
- **Answers direction questions:** on directed graphs, `mode="in"` or `mode="out"` counts only arriving or
  only departing edges ("how many airports have more than 100 departing routes?").
- **Compact, LLM-friendly output:** only degrees that occur are listed, as `{degree, count}` pairs sorted by
  degree. No zero-filled array to index into, and even airports' 173 distinct degrees fit in about 5 KB.
- **The summary answers on its own:** it gives the range, the mean and the most common degree, so an LLM
  often needs nothing else.

## When to use it
Questions about the whole network's connectivity, not one node:
- "Do most members of the karate club have only a few friends?"
- "Is the airport network dominated by a few hubs?"
- "How many airports have exactly two departing routes?" (`mode="out"`)

For one node's degree, use node_degree; for the top nodes by degree, use degree_centrality.

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| mode | string | `total` | On directed graphs: `total` (in + out), `in` (edges arriving) or `out` (edges leaving). Undirected graphs accept only `total`. |

## Output
`result` is one object. Example for `{"graph_id": "karate"}`:

```json
{"mode": "total", "num_nodes": 34, "min_degree": 1, "max_degree": 17, "mean_degree": 4.588235,
 "histogram": [{"degree": 1, "count": 1}, {"degree": 2, "count": 11}, {"degree": 3, "count": 6}, "...",
               {"degree": 16, "count": 1}, {"degree": 17, "count": 1}]}
```
Summary: *In 'karate', degree ranges from 1 to 17 with mean 4.588235 over 34 nodes; the most common degree is
2 (11 nodes).*

`mean_degree` is rounded to 6 decimals. No `result_graph_id`.

## Graphs it supports
All graphs: directed and undirected, weighted (weights ignored) and unweighted.

## Errors
Each returns `status: "error"` with a message saying how to fix the call:
- Unknown `graph_id`: use `list_graphs`.
- `mode` not one of `total`, `in`, `out`.
- `mode="in"` or `"out"` on an undirected graph: use `total`.
- Unknown parameter, or a graph with no nodes.

## How it is tested
14 tests in `tests/`:
- total-degree counts against `nx.degree_histogram` on all five graphs;
- in and out counts against NetworkX on airports;
- min, max and mean degree;
- sorted histogram with no zero counts;
- every error case and determinism.
