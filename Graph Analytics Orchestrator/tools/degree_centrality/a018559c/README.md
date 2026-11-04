# Degree Centrality

Ranks nodes by raw, unweighted degree. Directed graphs report `in_degree`, `out_degree`, and `degree` (their sum); undirected graphs report `degree`. Ties are ordered by node ID. Results are capped by `top_k` and the 8 KB response limit.

Run validation and tests from the graph-tools-starter directory:

```powershell
python -m graphkit.validate registry/tools/degree_centrality/a018559c
python -m pytest registry/tools/degree_centrality/a018559c/tests
```
