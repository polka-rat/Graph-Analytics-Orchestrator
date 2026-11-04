# motif_count

**Tier:** Hard  
**Author:** 37c243f2

Counts triangle motifs in undirected graphs and feed-forward loops in directed graphs. Each undirected triangle is counted once. A feed-forward loop follows A -> B, A -> C, and B -> C. The total count covers the graph; `top_k` limits only the returned examples.

Parameter: `graph_id` (required); `top_k` (optional positive integer, default `15`).
