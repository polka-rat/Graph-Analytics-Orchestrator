"""Enumerate the largest maximal cliques with pivoted Bron-Kerbosch."""
import json
import time

from graphkit.contract import check_top_k, error, get_graph, node_ref, ok
from graphkit.graph import Graph

MAX_OUTPUT_BYTES = 8 * 1024
SEARCH_SECONDS = 25
SAMPLE_NODES = 10


class _SearchTimedOut(Exception):
    pass


def _fits(result, summary, result_graph_id):
    response = ok(result, summary, result_graph_id=result_graph_id)
    return len(json.dumps(response, allow_nan=False, sort_keys=True).encode("utf-8")) <= MAX_OUTPUT_BYTES


def run(store, graph_id: str, top_k=10, **params) -> dict:
    try:
        g, err = get_graph(store, graph_id)
    except AttributeError:
        return error("store must provide get(graph_id). Pass the graph store supplied to the tool.")
    if err:
        return err
    if not isinstance(g, Graph):
        return error("The selected graph is not a supported Graph. Choose a graph returned by the graph store.")
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. Remove them; supported parameter is top_k.")
    k, err = check_top_k(top_k)
    if err:
        return err

    nodes = sorted(g.nodes())
    adjacency = {
        node: set(g.undirected_neighbors(node)).intersection(nodes) - {node}
        for node in nodes
    }
    largest = []
    deadline = time.monotonic() + SEARCH_SECONDS

    def record(clique):
        candidate = tuple(sorted(clique))
        largest.append(candidate)
        largest.sort(key=lambda item: (-len(item), item))
        del largest[k:]

    def bron_kerbosch(current, possible, excluded):
        if time.monotonic() >= deadline:
            raise _SearchTimedOut
        if not possible and not excluded:
            record(current)
            return
        pivot_candidates = possible | excluded
        pivot = None
        pivot_score = -1
        for candidate in sorted(pivot_candidates):
            score = len(possible & adjacency[candidate])
            if score > pivot_score:
                pivot = candidate
                pivot_score = score
        candidates = sorted(possible - (adjacency[pivot] if pivot is not None else set()))
        for node in candidates:
            bron_kerbosch(
                current | {node},
                possible & adjacency[node],
                excluded & adjacency[node],
            )
            possible.remove(node)
            excluded.add(node)

    try:
        if nodes:
            bron_kerbosch(set(), set(nodes), set())
    except _SearchTimedOut:
        return error(
            f"Maximal-clique search for '{graph_id}' exceeded {SEARCH_SECONDS} seconds. "
            "Use a smaller or sparser graph, or request fewer cliques with top_k."
        )
    except RecursionError:
        return error(
            f"Maximal-clique search for '{graph_id}' exceeded the safe recursion depth. "
            "Use a smaller graph or split it into smaller subgraphs."
        )

    if not largest:
        try:
            sub_id = store.subgraph(graph_id, [], f"Largest maximal cliques of '{graph_id}'")
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            return error(f"Could not register the empty clique result: {exc}. Check that graph_id is valid.")
        return ok([], f"Graph '{graph_id}' has no nodes and therefore no non-empty maximal cliques.",
                  result_graph_id=sub_id)

    result = []
    result_graph_id = None
    for index, clique in enumerate(largest, 1):
        try:
            sub_id = store.subgraph(graph_id, clique, f"Maximal clique {index} of '{graph_id}'")
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            return error(f"Could not register maximal clique {index}: {exc}. Check that graph_id is valid.")
        if result_graph_id is None:
            result_graph_id = sub_id

        refs = [node_ref(g, node) for node in clique]
        entry = {"size": len(clique), "nodes": refs, "graph_id": sub_id}
        candidate = result + [entry]
        summary = (f"Found {len(largest)} largest maximal clique(s) in '{graph_id}'; "
                   f"returning {len(candidate)}.")
        if _fits(candidate, summary, result_graph_id):
            result = candidate
            continue

        sampled_entry = {
            "size": len(clique),
            "nodes": refs[:SAMPLE_NODES],
            "nodes_truncated": len(refs) > SAMPLE_NODES,
            "graph_id": sub_id,
        }
        candidate = result + [sampled_entry]
        summary = (f"Found {len(largest)} largest maximal clique(s) in '{graph_id}'; "
                   f"returning {len(candidate)}.")
        if not _fits(candidate, summary, result_graph_id):
            if not result:
                return error("Clique metadata exceeds the 8 KB response limit. Use a graph with shorter node labels.")
            break
        result = candidate

    return ok(
        result,
        f"Found {len(largest)} largest maximal clique(s) in '{graph_id}'; returning {len(result)}.",
        result_graph_id=result_graph_id,
    )
