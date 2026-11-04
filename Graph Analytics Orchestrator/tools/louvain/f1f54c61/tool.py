
"""Detect communities using the Louvain method and modularity optimisation."""

from collections import defaultdict
from math import isfinite

from graphkit.contract import check_top_k, error, get_graph, node_ref, ok


TOL = 1e-12
MAX_PASSES = 100
MAX_LEVELS = 20
DISPLAY_LIMIT = 10


def modularity(adj, degree, community, total_weight):
    """Calculate modularity for an undirected weighted graph."""
    if total_weight <= 0:
        return 0.0

    internal_weight = defaultdict(float)
    community_degree = defaultdict(float)

    for node, group in community.items():
        community_degree[group] += degree[node]

        for neighbor, weight in adj[node].items():
            if community.get(neighbor) == group:
                internal_weight[group] += weight

    score = 0.0

    for group, degree_sum in community_degree.items():
        score += internal_weight[group] / (2.0 * total_weight)
        score -= (degree_sum / (2.0 * total_weight)) ** 2

    return score


def local_move(adj):
    """Move nodes to neighboring or singleton communities when modularity improves."""
    nodes = sorted(adj)
    community = {node: index for index, node in enumerate(nodes)}

    degree = {
        node: sum(adj[node].values())
        for node in nodes
    }
    total_weight = sum(degree.values()) / 2.0

    if total_weight <= 0:
        return community

    current_modularity = modularity(
        adj, degree, community, total_weight
    )

    # Fresh IDs are outside the initial range and never reused.
    next_group = len(nodes)

    for _ in range(MAX_PASSES):
        changed = False

        for node in nodes:
            old_group = community[node]

            candidates = {
                community[neighbor]
                for neighbor in adj[node]
                if neighbor != node
            }
            candidates.discard(old_group)

            # Allow a node to become a singleton if it improves modularity.
            community_members = sum(
                1 for group in community.values()
                if group == old_group
            )

            if community_members > 1:
                candidates.add(next_group)
                next_group += 1

            best_group = old_group
            best_score = current_modularity

            for candidate in sorted(candidates):
                community[node] = candidate

                score = modularity(
                    adj, degree, community, total_weight
                )

                if score > best_score + TOL:
                    best_group = candidate
                    best_score = score

            community[node] = best_group

            if best_group != old_group:
                current_modularity = best_score
                changed = True

        if not changed:
            break

    return community


def aggregate(adj, community, original_members):
    """Replace each community with a supernode."""
    groups = sorted(set(community.values()))
    aggregated = {group: defaultdict(float) for group in groups}
    members = {group: [] for group in groups}

    for node, group in community.items():
        members[group].extend(original_members[node])

        for neighbor, weight in adj[node].items():
            other_group = community[neighbor]
            aggregated[group][other_group] += weight

    return (
        {
            group: dict(neighbors)
            for group, neighbors in aggregated.items()
        },
        members,
    )


def _validate_weight(weight):
    """Return whether an edge weight is a finite, non-negative number."""
    if isinstance(weight, bool) or not isinstance(weight, (int, float)):
        return False

    try:
        return isfinite(float(weight)) and weight >= 0
    except (TypeError, ValueError, OverflowError):
        return False


def run(store, graph_id, top_k=10, **params):
    """Detect communities using multilevel modularity optimization."""
    g, err = get_graph(store, graph_id)
    if err:
        return err

    if params:
        return error(
            f"Unknown parameter(s): {', '.join(params)}."
        )

    k, err = check_top_k(top_k)
    if err:
        return err

    if g.directed:
        return error(
            "This Louvain implementation supports undirected graphs only. "
            "Use an undirected graph."
        )

    nodes = sorted(g.nodes())

    if not nodes:
        return error(
            "The graph is empty; provide a graph containing nodes."
        )

    # Build symmetric adjacency; represent a self-loop as 2 * its weight.
    adj = {node: {} for node in nodes}

    try:
        for u, v, weight in g.edges():
            if u not in adj or v not in adj:
                return error(
                    "The graph contains an edge with an unknown endpoint."
                )

            if not _validate_weight(weight):
                return error(
                    "Edge weights must be finite, non-negative numbers."
                )

            weight = float(weight)

            if u == v:
                adj[u][u] = adj[u].get(u, 0.0) + 2.0 * weight
            else:
                adj[u][v] = adj[u].get(v, 0.0) + weight
                adj[v][u] = adj[v].get(u, 0.0) + weight

    except (ValueError, KeyError, TypeError, OverflowError) as exc:
        return error(f"Could not read graph edges: {exc}")

    original_degree = {
        node: sum(adj[node].values())
        for node in nodes
    }
    total_weight = sum(original_degree.values()) / 2.0

    if total_weight <= 0:
        communities = [[node] for node in nodes]
        final_partition = {
            node: index for index, node in enumerate(nodes)
        }
        score = 0.0
    else:
        current_adj = adj
        original_members = {node: [node] for node in nodes}
        final_partition = {
            node: index for index, node in enumerate(nodes)
        }

        # Alternate local node movement and graph aggregation.
        for _ in range(MAX_LEVELS):
            partition = local_move(current_adj)

            groups = defaultdict(list)
            for node, group in partition.items():
                groups[group].append(node)

            # Map each current community back to original graph nodes.
            expanded_partition = {}
            for group, representatives in groups.items():
                for representative in representatives:
                    for original in original_members[representative]:
                        expanded_partition[original] = group

            final_partition = expanded_partition

            # No communities merged, so another level cannot help.
            if len(groups) == len(current_adj):
                break

            current_adj, original_members = aggregate(
                current_adj, partition, original_members
            )

            if len(current_adj) <= 1:
                break

        communities_by_id = defaultdict(list)
        for node in nodes:
            communities_by_id[final_partition[node]].append(node)

        communities = list(communities_by_id.values())

        # Score the final partition on the original graph.
        score = modularity(
            adj, original_degree, final_partition, total_weight
        )

    communities.sort(key=lambda members: (-len(members), members[0]))

    result = []
    largest_graph_id = None

    # Return at most top_k communities; display a compact node preview.
    for index, members in enumerate(communities[:k], start=1):
        try:
            subgraph_id = store.subgraph(
                graph_id,
                members,
                f"Louvain community {index} in {graph_id}",
            )
        except (ValueError, KeyError) as exc:
            return error(
                f"Could not register community subgraph: {exc}"
            )

        if index == 1:
            largest_graph_id = subgraph_id

        result.append({
            "community": index,
            "size": len(members),
            "nodes": [
                node_ref(g, node)
                for node in members[:DISPLAY_LIMIT]
            ],
            "graph_id": subgraph_id,
        })

   
    summary = (
        f"Louvain detected {len(communities)} communities among "
        f"{len(nodes)} nodes. Overall modularity: {score:.6f}. "
        f"Returning {len(result)} communities."
    )

    return ok(result, summary, result_graph_id=largest_graph_id)
