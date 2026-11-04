# motif_count

Author: 51616f3b
Tier: hard
Category: structure

## What it computes
This tool counts small 3-node subgraph patterns (motifs):

### 1. Undirected graphs
- **Triangle**: A 3-clique where all three nodes are mutually connected.
- **Open wedge**: A 2-hop path $u-v-w$ lacking an edge between $u$ and $w$.
- **Transitivity**: The ratio $3 \times \text{triangles} / \text{total\_wedges}$, where total wedges is $\sum \binom{d}{2}$.

### 2. Directed graphs (16-type triad census & derived motifs)
- Computes the standard Davis-Leinhardt 16-type triadic census using the Batagelj-Mrvar algorithm:
  `003`, `012`, `102`, `021D`, `021U`, `021C`, `111D`, `111U`, `030T`, `030C`, `201`, `120D`, `120U`, `120C`, `210`, `300`.
- **Feed-forward loop (induced)**: Strictly type `030T` (transitive triad with no extra reciprocal arcs).
- **Feed-forward loop (non-induced)**: Any configuration with a shortcut $a \to b \to c$ and $a \to c$, allowing extra edges. Calculated as:
  $$\text{FFL}_{\text{non-induced}} = \sum_{(a,b) \in E} |out(a) \cap out(b)|$$
  Identity checked against:
  $$\text{FFL}_{\text{non-induced}} = 030T + 2 \times 120U + 120C + 2 \times 120D + 3 \times 210 + 6 \times 300$$
- **Directed 3-cycle (induced)**: Strictly type `030C`.
- **Directed 3-cycle instances (non-induced)**: Cycles of length 3 where each distinct directed cycle counts separately:
  $$\text{cycle\_instances} = 030C + 120C + 210 + 2 \times 300$$
- **Node sets with directed cycle**: Sets of 3 nodes containing at least one directed cycle:
  $$\text{node\_sets} = 030C + 120C + 210 + 300$$
- **Mutual dyads**: Number of node pairs with reciprocal arcs ($u \to v$ and $v \to u$).

## Algorithm and 64-entry classifier
- **Undirected triangles**: Nodes are ordered by $(degree, id)$, edges are directed from lower to higher rank, and triangles are found by intersecting neighbor sets.
- **Directed triadic census**: Uses Batagelj-Mrvar's algorithm. For each edge $(v, u)$, it identifies the neighborhood union $s$ to count missing dyads (`012` and `102`), and encodes the 6 possible directed arcs among $(v, u, w)$ into a 6-bit mask ($2^6 = 64$ entries) to classify triples into one of the 16 types. Type `003` is determined by subtracting all active triples from $\binom{n}{3}$.

## Supported graphs
- Undirected graphs (karate, lesmis, projects).
- Directed graphs (airports, courses).
- Graphs with fewer than 3 nodes return status ok with 0 motif counts.
- Edge weights and self-loops are ignored.

## Parameters
- `graph_id` (string, required): ID of the graph to analyse.

## Output example (directed)
```json
{
  "status": "ok",
  "result": {
    "graph_type": "directed",
    "node_count": 500,
    "edge_count": 20058,
    "triad_census": {
      "003": 16245812,
      "012": 76940,
      "102": 3889873,
      "021D": 56,
      "021U": 93,
      "021C": 126,
      "111D": 8270,
      "111U": 8066,
      "030T": 1,
      "030C": 5,
      "201": 395079,
      "120D": 29,
      "120U": 35,
      "120C": 73,
      "210": 2494,
      "300": 81548
    },
    "feed_forward_loop_induced": 1,
    "directed_cycle_3_induced": 5,
    "feed_forward_loop_non_induced": 496972,
    "directed_cycle_3_non_induced_instances": 165668,
    "node_sets_with_directed_cycle": 84120,
    "mutual_dyads": 9932
  },
  "summary": "Graph 'airports' has 1 induced FFLs, 496972 non-induced FFLs, 5 induced 3-cycles, and 165668 non-induced cycle instances across 84120 node sets. Induced counts are often small in dense networks due to mutual connections.",
  "result_graph_id": null,
  "error": null
}
```

## What result_graph_id means
This tool computes motif statistics across the whole network and does not filter or generate a new subgraph. Therefore, `result_graph_id` is always `null`.

## Time complexity
- Undirected triangle counting: $O(m \sqrt{m})$.
- Directed triad census: $O(m \cdot d_{max})$, where $d_{max}$ is the maximum degree. On the 500-node `airports` dataset, it completes in around 0.3 seconds.

## Errors
- Unknown graph ID: returns an error instructing the user to check `list_graphs`.
- Unknown parameter: returns an error listing the unrecognized parameters.

## Running tests
From the repository root:
```bash
python -m pytest registry/tools/motif_count/51616f3b/tests
python -m graphkit.validate registry/tools/motif_count/51616f3b
```
