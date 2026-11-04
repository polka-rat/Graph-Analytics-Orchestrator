"""Detect communities using deterministic label propagation."""

from collections import Counter
import math

from graphkit.contract import check_top_k, error, get_graph, node_ref, ok


def run(store, graph_id, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}.")
    k, err = check_top_k(top_k)
    if err:
        return err

    # Initialize every node with its own label
    nodes = sorted(g.nodes())
    if not nodes:
        return error("The graph is empty; provide a graph containing nodes.")

    labels = {n: n for n in nodes}

    # Propagate labels in deterministic order until stable
    # The iteration limit prevents the algorithm from running indefinitely
    max_iterations = 100
    converged = False
    iterations = 0

    for iteration in range(1, max_iterations + 1):
        changed = False

        for node in nodes:
            # Directed graphs use only incoming neighbors
            if g.directed:
                neighbors = g.in_neighbors(node)
            # Undirected graphs use all adjacent nodes as neighbors
            else:
                neighbors = g.undirected_neighbors(node)

            if not neighbors:
                continue

            # Edge weights represent connection strength
            counts = Counter()
            for neighbor, weight in neighbors.items():
                # Weights must be real, finite, and non-negative.
                if isinstance(weight, bool):
                    return error("Edge weights must be finite, non-negative numbers.")
                try:
                    numeric_weight = float(weight)
                except (TypeError, ValueError, OverflowError):
                    return error("Edge weights must be finite, non-negative numbers.")

                if not math.isfinite(numeric_weight) or numeric_weight < 0:
                    return error("Edge weights must be finite, non-negative numbers.")

                # Zero-weight edges provide no influence on label selection.
                if numeric_weight == 0:
                    continue

                counts[labels[neighbor]] += numeric_weight

            # All incident edges may have zero weight.
            if not counts:
                continue

            highest_frequency = max(counts.values())

            # Deterministic tie breaking by choosing the label with the smallest ID
            best_label = min(
                label
                for label, count in counts.items()
                if count == highest_frequency
            )

            if labels[node] != best_label:
                labels[node] = best_label
                changed = True

        iterations = iteration
        if not changed:
            converged = True
            break

    # Group nodes by their final labels
    groups = {}
    for node in nodes:
        groups.setdefault(labels[node], []).append(node)

    # Largest communities first with ties broken by their smallest node ID
    communities = sorted(
        groups.values(),
        key=lambda members: (-len(members), members[0])
    )

    result = []
    largest_graph_id = None

    # Register each returned community as a subgraph
    for index, members in enumerate(communities[:k], start=1):
        try:
            subgraph_id = store.subgraph(
                graph_id,
                members,
                f"Label-propagation community {index} in {graph_id}"
            )
        except (ValueError, KeyError) as exc:
            return error(f"Could not register community subgraph: {exc}")

        if index == 1:
            largest_graph_id = subgraph_id

        # Limit displayed member nodes to keep the output within the 8 KB limit while preserving the full community size and subgraph
        result.append({
            "community": index,
            "label": labels[members[0]],
            "size": len(members),
            "nodes": [node_ref(g, n) for n in members[:10]],
            "graph_id": subgraph_id,
        })
    
    summary = (
        f"Label propagation found {len(communities)} communities among "
        f"{len(nodes)} nodes after {iterations} iterations. "
        f"{'Labels converged.' if converged else 'Maximum iterations reached.'} "
        f"Returning {len(result)} communities."
    )

    return ok(result, summary, result_graph_id=largest_graph_id)