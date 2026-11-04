# Label Propagation

Finds communities with seeded label propagation. For directed graphs, incoming and outgoing neighbors are combined as undirected adjacency. The result lists communities by size, includes labeled members (or a labeled sample when needed to stay below 8 KB), registers each returned community as a subgraph, and places the largest community's ID in `result_graph_id`.

Run validation and tests from the graph-tools-starter directory:

```powershell
python -m graphkit.validate registry/tools/label_propagation/a018559c
python -m pytest registry/tools/label_propagation/a018559c/tests
```
