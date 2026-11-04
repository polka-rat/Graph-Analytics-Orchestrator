# HITS Centrality Tool (`hits.98eff80e`)

**Author:** 98eff80e (Sriprakash T)  
**Tier:** Medium (2 Points)  
**Category:** Centrality  
**Implementation ID:** `hits.98eff80e`  

---

## 1. Overview & Algorithm

The `hits` tool implements Jon Kleinberg's seminal **Hyperlink-Induced Topic Search (HITS)** algorithm (1999) using power iteration. HITS evaluates nodes according to two complementary centrality scores through mutual reinforcement:

1. **Hub Score ($h$):** Measures the extent to which a node points to high-quality authority nodes.
2. **Authority Score ($a$):** Measures the extent to which a node is pointed to by high-quality hub nodes.

### Mathematical Formulation
Given an adjacency matrix $A$ where $A_{i,j}$ represents the weight (or 1.0 for unweighted graphs) of edge $i \to j$:

1. Initialize hub vector $h^{(0)} = \left(\frac{1}{N}, \dots, \frac{1}{N}\right)^T$.
2. In each iteration $k = 1, \dots, \text{max\_iter}$:
   $$\tilde{a}^{(k)} = (h^{(k-1)})^T A$$
   $$\tilde{h}^{(k)} = A \tilde{a}^{(k)}$$
   $$h^{(k)} = \frac{\tilde{h}^{(k)}}{\max(\tilde{h}^{(k)})}$$
3. Check convergence:
   $$\|h^{(k)} - h^{(k-1)}\|_1 < \text{tol}$$
4. Post-iteration normalization:
   - If `normalized=True` (default):
     $$h = \frac{h}{\sum h_i}, \quad a = \frac{a}{\sum a_i}$$
   - If `normalized=False`:
     $$a = \frac{a}{\max(a_i)}$$

This implementation matches NetworkX's reference implementation (`nx.hits` via `_hits_power_iteration`) to machine precision ($< 10^{-16}$).

---

## 2. Parameter Reference

| Parameter | Type | Required | Default | Range / Allowed | Description |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `graph_id` | `string` | **Yes** | — | Valid graph ID | Target graph to analyse from the store. |
| `top_k` | `integer` | No | `10` | `1` to `100` | Number of top-ranked nodes to return. |
| `score_type` | `string` | No | `"hub"` | `"hub"`, `"authority"` | Centrality metric used for primary ranking. |
| `max_iter` | `integer` | No | `100` | $\ge 1$ | Maximum number of power iterations. |
| `tol` | `number` | No | `1e-8` | $> 0$ | Error tolerance for power iteration convergence. |
| `normalized` | `boolean` | No | `true` | `true`, `false` | Whether to normalize scores so each sums to 1.0. |
| `weighted` | `boolean` | No | `true` | `true`, `false` | Whether to incorporate edge weights into matrix $A$. |

Any unrecognised parameter passed in `**params` returns a structured error.

---

## 3. Output Schema

The tool adheres strictly to the universal `graphkit` contract:

```json
{
  "status": "ok",
  "result": [
    {
      "id": "FRA",
      "label": "Frankfurt am Main Airport",
      "score": 0.014987,
      "hub_score": 0.014987,
      "authority_score": 0.013542
    }
  ],
  "summary": "Frankfurt am Main Airport (FRA) is the top hub with score 0.014987 (hub: 0.014987, authority: 0.013542) in 'airports'.",
  "result_graph_id": null,
  "error": null
}
```

- Each node entry is formatted using `node_ref(g, n, ...)` and includes `id`, `label`, `score`, `hub_score`, and `authority_score`.
- Floating-point scores are rounded to 6 decimal places.
- Tied scores are sorted deterministically using `(-round(primary_score, 6), node_id)`.
- If `top_k=100` on large graphs (such as `airports`), the output automatically stays strictly under the 8,192-byte limit (`MAX_OUTPUT_BYTES`).

---

## 4. Complexity & Performance

- **Time Complexity:** $O(\text{max\_iter} \times (|V| + |E|))$ using vectorized NumPy matrix multiplications.
- **Space Complexity:** $O(|V|^2)$ for dense adjacency representations.
- **Runtime:**
  - `airports` ($|V|=500$, $|E|=20,058$): $< 0.05$ seconds (14 iterations to converge).
  - `karate`, `lesmis`, `courses`, `projects`: $< 0.01$ seconds.
  - Well under the 30-second timeout threshold (and well under the 10-second warning limit).

---

## 5. Edge Cases Handled

1. **Unknown Graph ID:** Returns structured error via `get_graph()`.
2. **Invalid Parameters:** Type and bounds checking on `top_k`, `score_type`, `max_iter`, `tol`, `normalized`, and `weighted`.
3. **Edgeless Graphs ($|E| = 0$):** Returns score `0.0` for all nodes cleanly without zero-division exceptions.
4. **Non-Convergence:** Gracefully reports an error message if `max_iter` is exceeded without reaching tolerance.
5. **Determinism:** Independent runs on fresh `GraphStore` instances yield identical byte outputs.
