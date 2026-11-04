# link_prediction

**Tier:** Medium  
**Author:** 37c243f2

Ranks missing links using common-neighbor, Jaccard, or Adamic-Adar scores.

For directed graphs, incoming and outgoing neighbors are combined and treated as undirected. Existing edges in either direction are excluded. Only positive-scoring candidates are returned. Ties are broken by node IDs.

Parameters:
- `graph_id`: graph to analyze.
- `method`: `common_neighbors`, `jaccard`, or `adamic_adar` (default `adamic_adar`).
- `top_k`: maximum results to return, 1 to 100 (default `10`). Output is shortened if needed to stay under 8 KB.
