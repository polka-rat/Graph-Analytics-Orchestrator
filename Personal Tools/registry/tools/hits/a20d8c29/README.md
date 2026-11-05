# hits

**Author:** a20d8c29 · **Tier:** medium · **Category:** centrality

## What it computes
Kleinberg's HITS (Hyperlink-Induced Topic Search). Every node gets **two** scores, because
in a directed graph there are two ways to matter:

- **authority** — high when many good hubs point *at* you (a major destination).
- **hub** — high when you point *at* many good authorities (a connecting airport).

The two are defined in terms of each other:

    authority(v) = Σ hub(u)        over every edge u → v
    hub(u)       = Σ authority(v)  over every edge u → v

The tool solves this by **power iteration**: hub starts uniform at `1/n`, the two updates
are applied in turn, hub is rescaled by its maximum each round to stop it growing without
bound, and iteration stops when the total change in hub scores falls below `tol`. This
converges to the principal eigenvectors of AᵀA (authority) and AAᵀ (hub). The final two
vectors are each normalised to sum to 1.

Time complexity is **O(i · n²)** for `i` iterations using a dense adjacency matrix, which
is the right choice at this scale. On `airports` (500 nodes, 20,058 edges) it converges in
14 iterations and runs in about 0.07 s, far inside the 30 s limit.

Scores agree with `networkx.hits` to within 1e-6 on all five datasets, including the
weighted ones: like NetworkX, this implementation uses the **weighted** adjacency matrix
when the graph is weighted. Pass `use_weights=false` for the classic unweighted form.

## When to use it
Questions that distinguish *pointing at* from *being pointed at*:

- "Which airports are the best connecting hubs, rather than the biggest destinations?"
- "Which courses are the most depended-on in this prerequisite graph?"

For plain overall importance, `pagerank` is the better tool.

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| top_k | integer | 10 | How many results to return (1 to 100) |
| rank_by | string | `"authority"` | Which score orders the output: `"authority"` or `"hub"` |
| max_iter | integer | 100 | Maximum power-iteration rounds (1 to 10000) |
| tol | number | 1e-8 | Convergence tolerance, strictly between 0 and 1 |
| use_weights | boolean | true | Weight links by edge weight on a weighted graph |

## Output
`result` is a ranked list; every entry carries **both** scores. `result_graph_id` is always
`null`.

```json
[{"id": "FRA", "label": "Frankfurt am Main Airport", "authority": 0.014942, "hub": 0.014987}]
```

Scores are rounded to 6 decimal places. Ties are broken by node id in ascending order.

`top_k` is an upper bound. Because node labels can be long, 100 entries would overflow the
8 KB response limit on `airports`, so the lowest-ranked entries are dropped until the whole
response fits and the summary says how many were shown.

## Graphs it supports
Directed or undirected, weighted or unweighted, including subgraphs registered by other
tools. HITS is designed for directed graphs; on an undirected graph the adjacency matrix is
symmetric, so hub and authority scores come out identical and the summary says so.

## Errors
| Error | Cause |
| --- | --- |
| `No graph with id '...'. Use list_graphs ...` | Unknown `graph_id` |
| `Graph '...' has no nodes, so HITS has nothing to score.` | Empty graph |
| `Graph '...' has no edges. HITS scores nodes by who links to whom ...` | Edgeless graph: every score would be zero |
| `top_k must be a whole number from 1 to 100; got ...` | `top_k` out of range or not an integer |
| `max_iter must be a whole number from 1 to 10000; got ...` | Bad `max_iter` |
| `tol must be a number greater than 0 and less than 1; got ...` | Bad `tol` |
| `rank_by must be one of authority or hub; got ...` | Bad `rank_by` |
| `use_weights must be true or false; got ...` | Bad `use_weights` |
| `HITS did not converge on '...' within N iterations ...` | Hit `max_iter` first; raise `max_iter` or `tol` |
| `HITS did not produce usable scores ... hub values collapsed to zero` | Degenerate structure with no reciprocated paths |
| `Unknown parameter(s): ...` | A parameter not in the manifest |

## Tests
Ten tests in `tests/test_hits.py`: scores against `networkx.hits` on directed weighted
`airports` and on undirected `karate` and `lesmis`; hub equals authority when undirected;
`rank_by` reorders the output; ties ascend by node id; `top_k` and the 8 KB bound are both
respected; seven invalid inputs each return an error rather than crashing; non-convergence
at `max_iter=1` is reported; `use_weights=false` changes the ranking on a weighted graph;
and two identical runs give identical output.
