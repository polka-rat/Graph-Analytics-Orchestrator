# pagerank

**Author:** da50612d · **Tier:** medium · **Category:** centrality

## What it computes
PageRank scores every node by the chance that a random surfer is there: at each step the surfer follows an out-link with probability `damping` (choosing links in proportion to their weight), and otherwise jumps to a node chosen uniformly at random. Nodes without out-links (dangling nodes) send their score uniformly to every node. The scores sum to 1.

The tool runs power iteration on the row-normalised adjacency matrix P (NumPy): it starts from x = 1/N and repeats `x ← d·(x·P + (Σ dangling x)/N) + (1 − d)/N` until the L1 change drops below `N·tol`. This is the same update, start vector and stopping rule as `networkx.pagerank`, so the scores agree with NetworkX to rounding. Each iteration costs O(N²) with the dense matrix (O(N + E) work in principle). `airports` (N = 500) converges in 10 to 15 iterations, in about 5 ms.

## When to use it
Questions about overall importance or influence, where a link from an important node counts more than a link from a minor one:
- "Which airports are the most important hubs in the network?"
- "Who are the most influential members of the karate club?"
- "Which courses are the most important in the catalogue?"

For simple "most connections" questions, degree centrality is more direct.

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of the graph |
| damping | number | 0.85 | Probability of following a link; strictly between 0 and 1 |
| top_k | integer | 10 | How many top-ranked nodes to return (1 to 100) |
| weighted | boolean | true | Split a node's score over its out-links in proportion to edge weight (NetworkX's default); false counts every link equally |
| max_iter | integer | 100 | Maximum number of iterations (1 to 10000) |
| tol | number | 1e-6 | Convergence tolerance (stop when the L1 change < N·tol) |

## Output
`result` is a list of the top_k nodes, highest score first. Equal scores are ordered by node id, and scores are rounded to 6 decimals:
```json
[{"id": "FRA", "label": "Frankfurt am Main Airport", "score": 0.013775},
 {"id": "CDG", "label": "Charles de Gaulle International Airport", "score": 0.012764}]
```
The summary names the top node and gives the damping, whether weights were used, the number of iterations, and the number of dangling nodes. If `top_k` entries would push the response past 8 KB (long airport names), the list is shortened, and the summary says how many entries are shown. `result_graph_id` is always `null`.

## Graphs it supports
Directed graphs (rank flows along edge direction) and undirected graphs (each edge works both ways), weighted or unweighted, including subgraphs registered by other tools. Note that on `airports` the weight is the route distance, so the default weighted ranking favours long-haul links; use `weighted=false` to rank by route structure alone.

## Errors
| Error | Why |
| --- | --- |
| `No graph with id '…'` | Unknown `graph_id`; use `list_graphs` |
| `damping must be a number strictly between 0 and 1` | Bad `damping` |
| `top_k must be a whole number from 1 to 100` | Bad `top_k` |
| `weighted must be true or false` | `weighted` is not a boolean |
| `max_iter must be…` / `tol must be…` | Bad iteration settings |
| `PageRank did not converge within … iterations` | Stopped before converging; raise `max_iter` or `tol` |
| `… negative edge weights …` | Weighted PageRank needs non-negative weights; use `weighted=false` |
| `Unknown parameter(s): …` | A parameter this tool does not take |
| `Graph '…' has no nodes` | Empty graph |
