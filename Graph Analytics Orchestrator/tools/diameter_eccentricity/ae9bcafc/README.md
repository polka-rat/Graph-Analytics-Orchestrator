# diameter_eccentricity - ae9bcafc

This tool runs breadth-first search from every node to compute unweighted eccentricities.
The largest eccentricity is the diameter, the smallest is the radius, and nodes attaining
those values form the periphery and center respectively.

Directed graphs use directed reachability and therefore must be strongly connected.
Undirected graphs must be connected. A disconnected graph returns a clear error because
its whole-graph diameter is not finite under the assignment's definition. Edge weights are
ignored; use a weighted-path tool for metric distances.

The result contains `diameter`, `radius`, bounded labelled `center` and `periphery` lists,
their full counts and truncation flags. Supplying `node` additionally returns that node's
eccentricity. Lists are sorted by node id and capped by `top_k` and the 8 KB response rule.

Time is `O(V(V + E))`; auxiliary space is `O(V + E)`.

```bash
python run_tool.py registry/tools/diameter_eccentricity/ae9bcafc graph_id=karate node=m1 top_k=10
```
