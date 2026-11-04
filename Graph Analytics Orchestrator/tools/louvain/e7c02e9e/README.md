
# louvain

**Author:** e7c02e9e · **Tier:** hard · **Category:** community (returns `result_graph_id`)

## What it computes

Finds communities in a graph by optimising modularity, using the Louvain algorithm introduced by Blondel, Guillaume, Lambiotte and Lefebvre (2008). The algorithm is implemented from scratch.

The algorithm has two main phases:

1. **Local moving:** Initially, every node belongs to its own community. Nodes are visited in a seeded random order, and each node may move into a neighbouring community if the move improves modularity. This process repeats until a complete pass makes no improving moves.
2. **Aggregation:** Each community is collapsed into a single weighted node. Edges between communities become edges between the corresponding new nodes, and internal edges are represented as self-loops. The local-moving phase is then repeated on the smaller graph.

The process stops when the local-moving phase cannot improve the partition further.

The implementation runs eight seeded restarts and retains the partition with the highest modularity. The supplied `seed` controls these restarts, making the result deterministic for the same graph and parameters.

Each local-moving pass examines nodes and their incident edges, giving roughly O(V + E) work per pass. The complete runtime depends on the number of passes and aggregation levels.

The returned `modularity` is standard Newman modularity at resolution 1.0, calculated using edge weights when they are enabled. Higher modularity generally indicates stronger community structure. Values above about 0.3 are often considered evidence of clear community structure, although the interpretation depends on the graph.

## When to use it

- "What are the communities in the karate club, and how strong are they?"
- "Which community does Valjean belong to?" (pass `node`)
- "What natural groups exist in this network?"
- "How clustered is the airport network?"
- Run another tool on `result_graph_id` or on a particular community's `graph_id` to analyse that part of the graph.

## Parameters

| Name | Type | Default | Meaning |
|---|---|---|---|
| `graph_id` | string | Required | ID of the graph to analyse |
| `resolution` | number | 1.0 | Must be positive. Larger values generally favour more and smaller communities; smaller values generally favour fewer and larger communities |
| `use_weights` | boolean | true | Use edge weights as connection strengths when the graph is weighted |
| `seed` | integer | 0 | Controls the node visitation order and seeded restarts |
| `top_k` | integer | 10 | Maximum number of largest communities to list in detail, from 1 to 100 |
| `node` | string | None | Optional node ID. If supplied, also reports its community and ensures that community is listed, even when it is outside the top `top_k` |

## Output

The `result` is a dictionary with the following structure:

```json
{
  "num_communities": 4,
  "modularity": 0.419790,
  "resolution": 1.0,
  "listed": 4,
  "communities": [
    {
      "community": 1,
      "size": 12,
      "graph_id": "karate~1",
      "members": [
        {
          "id": "m34",
          "label": "Member 34"
        }
      ]
    }
  ],
  "node_community": {
    "id": "m1",
    "label": "Member 1 (instructor)",
    "community": 2,
    "size": 11
  }
}
```

The values above are illustrative.

- `num_communities`: Number of communities in the full partition.
- `modularity`: Standard modularity of the returned partition.
- `resolution`: Resolution parameter used during optimisation.
- `listed`: Number of communities included in the output.
- `communities`: The listed communities, ordered by decreasing size, with ties broken by the smallest member ID.
- `community`: Community number, starting from 1.
- `size`: Number of nodes in that community.
- `graph_id`: ID of the registered subgraph containing that community.
- `members`: Up to five representative nodes with the highest number of neighbours; ties are broken by node ID. Fewer members may be returned when needed to meet the output-size limit.
- `node_community`: Included only when `node` is supplied. Identifies that node's community and its size.

If a requested node belongs to a community outside the largest `top_k`, that community is also listed. Consequently, `listed` may be greater than `top_k` by one.

`result_graph_id` identifies the largest community's registered subgraph. Each listed community is registered as an induced subgraph, containing its members and the edges among them.

The tool keeps its response below the assignment's 8 KB output limit by reducing the number of representative members and, if needed, the number of listed communities.

## Graphs it supports

- **Undirected graphs:** Analysed directly.
- **Directed graphs:** Accepted, but edge directions are ignored using the graph store's undirected-neighbour representation. Where reciprocal edges have different weights, that representation determines the combined undirected connection.
- **Weighted graphs:** Edge weights are used when `use_weights=true` and the graph is weighted.
- **Distance or cost weights:** Use `use_weights=false` when larger weights do not mean stronger connections.
- **Isolated nodes:** Nodes with no connections become one-node communities when the graph also contains edges.
- **Graphs without edges:** The tool returns an error when the entire graph has no edges, because there is no network structure to cluster.

The graph store allows registered community subgraphs to be used as input to other tools.

## Errors

The tool returns `status: "error"` with a helpful message for cases such as:

- Unknown graph ID.
- Unknown node ID; the error points to `lookup_node`.
- Non-positive or invalid resolution.
- A non-integer random seed.
- `top_k` outside the range 1 to 100.
- An unrecognised parameter.
- An edge weight less than or equal to zero when weights are enabled.
- A graph or subgraph with no edges.
