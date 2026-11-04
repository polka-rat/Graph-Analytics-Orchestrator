"""Detect communities with seeded label propagation."""
import json
import random
from collections import Counter, defaultdict

from graphkit.contract import check_top_k, error, get_graph, node_ref, ok
from graphkit.graph import Graph

MAX_OUTPUT_BYTES = 8 * 1024
SAMPLE_NODES = 10


def _fits(result, summary, result_graph_id):
    response = ok(result, summary, result_graph_id=result_graph_id)
    return len(json.dumps(response, allow_nan=False, sort_keys=True).encode("utf-8")) <= MAX_OUTPUT_BYTES


def run(store, graph_id: str, top_k=10, seed=0, **params) -> dict:
    try:
        g, err = get_graph(store, graph_id)
    except AttributeError:
        return error("store must provide get(graph_id). Pass the graph store supplied to the tool.")
    if err:
        return err
    if not isinstance(g, Graph):
        return error("The selected graph is not a supported Graph. Choose a graph returned by the graph store.")
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. Remove them; supported parameters are top_k and seed.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if isinstance(seed, bool) or not isinstance(seed, int):
        return error("seed must be an integer. Use seed=0 for deterministic default behavior.")

    nodes = g.nodes()
    labels = {node: node for node in nodes}
    neighbors = {node: set(g.undirected_neighbors(node)) - {node} for node in nodes}
    rng = random.Random(seed)
    max_iterations = max(1, min(1000, len(nodes) * 2))
    for _ in range(max_iterations):
        order = list(nodes)
        rng.shuffle(order)
        changed = False
        for node in order:
            if not neighbors[node]:
                continue
            counts = Counter(labels[neighbor] for neighbor in neighbors[node])
            highest = max(counts.values())
            tied = sorted(label for label, count in counts.items() if count == highest)
            selected = rng.choice(tied)
            if selected != labels[node]:
                labels[node] = selected
                changed = True
        if not changed:
            break

    groups = defaultdict(list)
    for node in nodes:
        groups[labels[node]].append(node)
    communities = [tuple(sorted(group)) for group in groups.values()]
    communities.sort(key=lambda group: (-len(group), group))

    if not communities:
        try:
            sub_id = store.subgraph(graph_id, [], f"Label propagation communities of '{graph_id}'")
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            return error(f"Could not register the empty community result: {exc}. Check that graph_id is valid.")
        return ok([], f"Label propagation found no nodes in '{graph_id}'.", result_graph_id=sub_id)

    result = []
    result_graph_id = None
    for index, community in enumerate(communities[:k], 1):
        try:
            sub_id = store.subgraph(graph_id, community, f"Label propagation community {index} of '{graph_id}'")
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            return error(f"Could not register community {index}: {exc}. Check that graph_id is valid.")
        if result_graph_id is None:
            result_graph_id = sub_id

        refs = [node_ref(g, node) for node in community]
        candidate_entry = {
            "community": index,
            "size": len(community),
            "graph_id": sub_id,
            "nodes": refs,
        }
        candidate = result + [candidate_entry]
        summary = (f"Label propagation found {len(communities)} communities in '{graph_id}'; "
                   f"returning {len(candidate)}.")
        if _fits(candidate, summary, result_graph_id):
            result = candidate
            continue

        sampled_entry = {
            "community": index,
            "size": len(community),
            "graph_id": sub_id,
            "nodes": refs[:SAMPLE_NODES],
            "nodes_truncated": len(refs) > SAMPLE_NODES,
        }
        candidate = result + [sampled_entry]
        summary = (f"Label propagation found {len(communities)} communities in '{graph_id}'; "
                   f"returning {len(candidate)}.")
        if not _fits(candidate, summary, result_graph_id):
            if not result:
                return error("Community metadata exceeds the 8 KB response limit. Use a graph with shorter node labels.")
            break
        result = candidate

    return ok(
        result,
        f"Label propagation found {len(communities)} communities in '{graph_id}'; returning {len(result)}.",
        result_graph_id=result_graph_id,
    )
