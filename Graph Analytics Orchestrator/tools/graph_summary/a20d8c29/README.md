# graph_summary

**Author:** a20d8c29 · **Tier:** easy · **Category:** structure

## What it computes
A single statistics report describing the whole graph: node and edge counts, density,
average degree, minimum and maximum degree, the number of isolated nodes, the number of
self-loops, and the most connected node. Directed graphs additionally report average and
maximum in-degree and out-degree; weighted graphs additionally report total, average,
minimum and maximum edge weight.

Density is the fraction of possible edges that are present. A directed pair of nodes has
two possible slots and an undirected pair only one, so

    directed:    density = m / (n(n-1))
    undirected:  density = 2m / (n(n-1))

For `n < 2` the denominator is zero and the density is reported as `0.0`, the same
convention as `networkx.density`. Average degree is `2m / n` on both kinds of graph,
because every edge contributes one out-stub and one in-stub.

Time complexity is **O(n + m)**: one pass over the nodes for degrees and one pass over the
edges for weights. On `airports` (500 nodes, 20,058 edges) it runs in well under a second.

## When to use it
Orientation questions, and as a cheap first call before choosing a more specific tool:

- "How big is this network?"
- "Is this graph dense or sparse, and how many connections does a typical node have?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph to summarise |

There is no `top_k`: the tool describes the whole graph rather than ranking nodes. Any
other parameter is rejected with an error.

## Output
`result` is one object, not a list. `result_graph_id` is always `null`.

```json
{
  "graph_id": "karate",
  "directed": false,
  "weighted": false,
  "nodes": 34,
  "edges": 78,
  "density": 0.139037,
  "average_degree": 4.588235,
  "min_degree": 1,
  "max_degree": 17,
  "isolated_nodes": 0,
  "self_loops": 0,
  "most_connected": {"id": "m34", "label": "Member 34 (administrator)", "degree": 17}
}
```

Directed graphs also carry `average_out_degree`, `average_in_degree`, `max_out_degree` and
`max_in_degree`. Weighted graphs also carry `total_edge_weight`, `average_edge_weight`,
`min_edge_weight` and `max_edge_weight`. All floats are rounded to 6 decimal places.

On a directed graph `most_connected.degree` is the total degree, in-degree plus out-degree.
Ties for the most connected node are broken by node id in ascending order, so the output is
deterministic.

## Graphs it supports
All of them: directed or undirected, weighted or unweighted, including subgraphs registered
by other tools. An empty graph returns a valid report with zeroes and
`"most_connected": null` rather than an error.

## Errors
| Error | Cause |
| --- | --- |
| `No graph with id '...'. Use list_graphs to see the available graphs.` | `graph_id` is not a known graph |
| `graph_id must be a string. Use list_graphs to see the available graphs.` | `graph_id` was not a string |
| `Unknown parameter(s): ... graph_summary takes only graph_id; ...` | Any parameter other than `graph_id` was passed, for example `top_k` |

## Tests
Seven tests in `tests/test_graph_summary.py`, checking counts and density against NetworkX
on the undirected `karate` and the directed `airports`, the most connected node and its
tie-break against NetworkX degrees on `lesmis`, which fields appear for
directed/weighted graphs, both error paths, and determinism across two runs.
