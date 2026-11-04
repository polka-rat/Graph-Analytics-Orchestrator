# motif_count

**Author:** 81c01533 · **Tier:** hard · **Category:** structure

## What it computes
Counts 3-node patterns (motifs).

- **Directed graphs:** the full 16-type triad census, matching `networkx.triadic_census`. Every group of 3 nodes is classified by its exact set of edges (for example `030T` is a feed-forward loop a→b, b→c, a→c, and `030C` is a cycle a→b→c→a). It uses the Batagelj–Mrvar algorithm: it only visits groups with at least one edge and gets the empty groups (`003`) by subtraction, so it runs in about O(E · d_max) and not O(V³).
- **Undirected graphs:** triangles and open triads (three nodes joined by exactly two edges). Triangles are counted by intersecting the neighbour sets at each edge; open triads are the 2-edge paths minus the 3 contained in each triangle. Time is about O(E · d_max).

## When to use it
Questions about which small building blocks a network is made of, and how clustered or hierarchical it is.
- "Which small patterns are most common in the airports network?"
- "How many triangles are there in the karate club graph, and who is in the most?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| top_k | integer | 10 | How many top nodes to return (1 to 100); only used on undirected graphs |

## Output
`result` contains:
- `motifs`: every motif as `{"motif", "name", "count"}`, most common first. Directed graphs list all 16 triad types (code and readable name); undirected graphs list `triangle` and `open_triad`.
- `top_nodes` (undirected graphs only): up to `top_k` nodes as `node_ref` (`id`, `label`) plus `triangles`, the number of triangles the node is part of (same as `networkx.triangles`). Nodes in no triangle are left out. These are the nodes at the centre of tight-knit groups. Directed graphs have no `top_nodes`, since per-node counts of exact triad types are too sparse to be useful (airports has only one pure feed-forward loop).

```json
{
  "motifs": [
    {"motif": "open_triad", "name": "open_triad", "count": 393},
    {"motif": "triangle", "name": "triangle", "count": 45}
  ],
  "top_nodes": [
    {"id": "m1", "label": "Member 1 (instructor)", "triangles": 18}
  ]
}
```

The summary names the most common connected pattern (ignoring `003`, `012` and `102`, which do not link all three nodes). The tool does not return a `result_graph_id`. Output is deterministic.

## Graphs it supports
- Directed and undirected graphs.
- Weighted and unweighted graphs; weights are ignored.
- Self-loops are ignored.

## Errors
The tool returns an error (never raises) when:
- `graph_id` does not exist.
- An unknown parameter is passed.
- `top_k` is not an integer from 1 to 100.
