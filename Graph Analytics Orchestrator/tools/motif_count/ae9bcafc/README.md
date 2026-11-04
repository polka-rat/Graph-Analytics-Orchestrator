# motif_count - ae9bcafc

This tool returns exact counts of common motifs in simple directed or undirected graphs.
Weights and self-loops do not affect the counts.

For every graph it reports:

- `triangles`: unordered triples whose three node pairs are adjacent. For a directed graph,
  adjacency is taken in the undirected projection.
- `open_triads`: unordered triples with exactly two adjacent node pairs.

For a directed graph it additionally reports:

- `feed_forward_loops`: ordered triples `(u, v, w)` with `u->v`, `v->w`, and `u->w`.
- `directed_3_cycles`: cyclic triples `u->v->w->u`, counted once per orientation.
- `reciprocal_pairs`: unordered node pairs having edges in both directions.

The definitions intentionally count distinct directed orientations. Thus a fully
bidirectional three-node clique contains six feed-forward loops and two directed cycles.
The implementation uses neighbour-set intersections rather than enumerating every node
triple, making it suitable for the supplied airports graph.

```bash
python run_tool.py registry/tools/motif_count/ae9bcafc graph_id=airports
```
