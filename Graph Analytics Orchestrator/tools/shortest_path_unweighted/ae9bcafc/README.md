# shortest_path_unweighted - ae9bcafc

This tool uses breadth-first search to return a minimum-hop path between two nodes.
For a directed graph it follows outgoing edges, while for an undirected graph it follows
ordinary neighbours. Edge weights are intentionally ignored.

## Parameters

- `graph_id`: graph to query.
- `source`: exact starting node id.
- `target`: exact destination node id.

The result contains labelled source and target references, a labelled `path`, and equal
integer fields `hops` and `distance`. Equal-length alternatives are resolved
deterministically by ascending node id. Missing nodes and unreachable destinations return
a contract error with recovery guidance.

## Complexity

Time is `O(V + E)` and auxiliary space is `O(V)`.

## Example

```bash
python run_tool.py registry/tools/shortest_path_unweighted/ae9bcafc graph_id=karate source=m1 target=m34
```
