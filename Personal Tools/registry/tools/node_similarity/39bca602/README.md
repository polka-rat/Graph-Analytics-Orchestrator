# node_similarity

**Author:** 39bca602 · **Tier:** easy · **Category:** structure

## What it computes
Computes Jaccard similarity and common neighbor overlap between graph nodes:
$$J(u, v) = \frac{|\Gamma(u) \cap \Gamma(v)|}{|\Gamma(u) \cup \Gamma(v)|}$$
In pairwise mode, it inspects two specified nodes. In ranking mode, it leverages an inverted 2-hop neighbor index to evaluate all candidates sharing at least one connection in $O\left(\sum_{w \in \Gamma(u)} d(w)\right)$ time.

## When to use it
- "How similar are the flight destinations of Chennai and Mumbai?"
- "Which members of the karate club share the most connections with John A?"

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| `graph_id` | string | (required) | Graph identifier |
| `node` | string | (required) | Reference node ID |
| `target_node` | string | null | Optional node ID for pairwise comparison |
| `direction` | string | "undirected" | Traversal direction ('undirected', 'out', 'in') |
| `top_k` | integer | 10 | Maximum top ranking entries to return (1 to 100) |

## Output
Returns a structured JSON payload containing similarity metrics and node references. Outputs strictly respect the 8 KB limit. Does not generate subgraphs (`result_graph_id` is null).

## Graphs it supports
Works across all directed, undirected, weighted, and unweighted graphs.

## Errors
- Unknown `graph_id` (suggests `list_graphs`)
- Unknown `node` or `target_node` (suggests `lookup_node`)
- Invalid `top_k` or unrecognized parameters