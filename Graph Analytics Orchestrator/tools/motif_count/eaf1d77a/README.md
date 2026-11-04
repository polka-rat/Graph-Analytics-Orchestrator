# motif_count (hard)

Counts small subgraph patterns.

## Motifs reported
| motif | graphs | meaning |
| --- | --- | --- |
| `triangle` | all (undirected view) | 3 nodes all linked |
| `wedge` | all | path u – v – w (Σ C(d, 2)) |
| `open_wedge` | all | wedge whose ends are not linked (wedges − 3·triangles) |
| `star3` | all | centre node with 3 neighbours (Σ C(d, 3)) |
| `cycle4` | all | 4-cycle a – b – c – d – a (chords allowed) |
| `feed_forward_loop` | directed | a→b, b→c, a→c (triad 030T) |
| `cycle3` | directed | a→b→c→a (triad 030C) |

The tool also returns the **transitivity** (3·triangles / wedges, as `nx.transitivity`) and the `top_k` nodes in the most triangles (as `nx.triangles`). For directed graphs it adds the full **16-type triad census** (as `nx.triadic_census`). With `node`, it also reports that node's triangle count.

## Algorithms
- **Triangles:** order the nodes by id. For each edge (u, v) with u < v, check the smaller neighbour set for common neighbours w > v. Each triangle is found exactly once, in O(Σ_edges min(d(u), d(v))).
- **4-cycles:** for each node u, count the 2-paths u – w – x to every later node x. A 4-cycle is two such paths between its opposite corners, and it has two diagonals, so the count is ½ · Σ C(c(u, x), 2).
- **Triad census:** Batagelj & Mrvar (2001). For each connected pair (v, u) with v < u, the triads {v, u, x} where x touches neither are counted in bulk (type 012 or 102). Each connected triad is classified once with a 6-bit code and a 64-entry lookup table. Type 003 is C(n, 3) minus all the others. The cost is O(m · Δ), not O(n³).
- **Lookup table:** built at import time by classifying each 3-node digraph from its mutual/asymmetric/null dyad counts and the direction of its arcs. A test checks every entry against `nx.triad_type`.

## Output and errors
Counts are integers and transitivity is rounded to 6 decimals. Top nodes are ordered by triangle count (descending), then id. Responses stay under 8 KB. An unknown graph, an unknown node, a bad `top_k` or an empty graph each return `status: "error"`.

## Example
```
python run_tool.py registry/tools/motif_count/STUDENT_ID graph_id=karate node=m1
python run_tool.py registry/tools/motif_count/STUDENT_ID graph_id=airports top_k=5
```
