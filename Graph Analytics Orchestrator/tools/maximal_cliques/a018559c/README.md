# Maximal Cliques

Uses pivoted Bron-Kerbosch to enumerate maximal cliques, then returns the largest ones in descending size order with deterministic ID tie-breaking. Directed graphs are treated as undirected for clique membership. Every returned clique is registered as a subgraph; `result_graph_id` points to the largest returned clique. Search is bounded to 25 seconds to protect the tool runtime, and oversized member lists are represented by labeled samples.

Run validation and tests from the graph-tools-starter directory:

```powershell
python -m graphkit.validate registry/tools/maximal_cliques/a018559c
python -m pytest registry/tools/maximal_cliques/a018559c/tests
```
