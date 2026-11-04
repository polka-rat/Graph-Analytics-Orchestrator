"""Link prediction: ranks pairs of unconnected nodes by how likely they are to become connected.

Rules (the validator checks them):
- Implement the algorithm yourself: standard library, NumPy and graphkit only.
- Get graphs only from the store; never open files, print, or use the network.
- Never crash: return error("what went wrong and how to fix it") instead.
- Return every node as node_ref(g, node, ...), so it has both an id and a label.
- Keep the output under 8 KB: respect top_k.
- Be deterministic: same input, same output. Randomised algorithms take a `seed` parameter (default 0).
"""
import heapq
import json
import math

from graphkit.contract import MAX_OUTPUT_BYTES, check_node, check_top_k, error, get_graph, node_ref, ok

METHODS = ("adamic_adar", "common_neighbors", "jaccard", "resource_allocation",
           "preferential_attachment", "community_resource_allocation")
MAX_ALL_PAIRS_NODES = 2000  # searching every pair of nodes is only done on graphs up to this size


def _neighbourhoods(g, use_direction):
    """left[x] = nodes x links to, right[x] = nodes linking to x, degree[x] = number of links of x.

    Without direction both sets are simply the neighbours of x."""
    left, right, degree = {}, {}, {}
    for x in g.nodes():
        if use_direction:
            left[x] = set(g.out_neighbors(x)) - {x}
            right[x] = set(g.in_neighbors(x)) - {x}
            degree[x] = len(left[x]) + len(right[x])
        else:
            left[x] = right[x] = set(g.undirected_neighbors(x)) - {x}
            degree[x] = len(left[x])
    return left, right, degree


def _scorer(method, left, right, degree, community):
    """Returns score(u, v) for the chosen method; the common neighbours of u -> v are left[u] & right[v]."""
    def score(u, v):
        common = left[u] & right[v]
        if method == "common_neighbors":
            return len(common)
        if method == "jaccard":
            union = len(left[u] | right[v])
            return len(common) / union if union else 0.0
        if method == "resource_allocation":
            return sum(1 / degree[w] for w in common)
        if method == "adamic_adar":
            return sum(1 / math.log(degree[w]) for w in common)
        if method == "preferential_attachment":
            return len(left[u]) * len(right[v])
        # community_resource_allocation: only pairs in the same community, counting common neighbours in it
        if community[u] != community[v]:
            return 0.0
        return sum(1 / degree[w] for w in common if community[w] == community[u])
    return score


def run(store, graph_id, node=None, method="adamic_adar", community_attribute=None, use_direction=False,
        top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}.")
    k, err = check_top_k(top_k)
    if err:
        return err
    # Useful Graph methods:
    #   g.nodes(), g.number_of_nodes(), g.number_of_edges(), g.directed, g.weighted
    #   g.out_neighbors(n), g.in_neighbors(n), g.undirected_neighbors(n)   -> {neighbour: weight}
    #   g.edges() -> (u, v, weight), g.weight(u, v), g.label(n), g.node_attrs(n)
    if method not in METHODS:
        return error(f"method must be one of {', '.join(METHODS)}; got {method!r}.")
    if not isinstance(use_direction, bool):
        return error("use_direction must be true or false.")
    if node is not None:
        err = check_node(g, node)
        if err:
            return err
    nodes = sorted(g.nodes())
    if node is None and len(nodes) > MAX_ALL_PAIRS_NODES:
        return error(f"Graph '{graph_id}' has {len(nodes)} nodes, too many to rank every pair. "
                     f"Give a node to get the best new links for that node.")

    # Step 1: for the community method, read each node's community from a node attribute (e.g. club, country).
    community = None
    if method == "community_resource_allocation":
        available = sorted(a for a in g.node_attrs(nodes[0]) if a != "label") if nodes else []
        if community_attribute not in available:
            return error(f"method 'community_resource_allocation' needs community_attribute, the name of a node "
                         f"attribute that groups nodes. Available attributes in '{graph_id}': "
                         f"{', '.join(available) if available else 'none (use another method)'}.")
        community = {n: g.node_attrs(n).get(community_attribute) for n in nodes}

    # Step 2: neighbour sets. Direction is only used on directed graphs when asked for.
    use_direction = use_direction and g.directed
    left, right, degree = _neighbourhoods(g, use_direction)
    score = _scorer(method, left, right, degree, community)

    # Step 3: candidate pairs are the pairs with no link yet (for one node: its non-neighbours).
    def candidates():
        if node is not None:
            for v in nodes:
                if v != node and v not in left[node]:
                    yield node, v
        elif use_direction:
            for u in nodes:
                for v in nodes:
                    if u != v and v not in left[u]:
                        yield u, v
        else:
            for i, u in enumerate(nodes):
                for v in nodes[i + 1:]:
                    if v not in left[u]:
                        yield u, v

    # Step 4: score every candidate and keep the best k (highest score first, ties by node ids ascending).
    counter = [0]

    def scored():
        for u, v in candidates():
            counter[0] += 1
            yield -round(float(score(u, v)), 6), u, v

    best = heapq.nsmallest(k, scored())
    way = ""
    if g.directed:
        way = " Link direction is followed." if use_direction else " Link direction is ignored."
    how = f"{method}" + (f" ({community_attribute})" if community is not None else "")
    if not best:
        return ok([], f"No missing links to predict: every candidate pair is already linked.{way}")

    # Step 5: build the output, listing fewer pairs if it would be over the 8 KB limit.
    def build(shown):
        if node is not None:
            result = [node_ref(g, v, score=-neg) for neg, _, v in best[:shown]]
            first = f"{result[0]['label']} ({result[0]['id']})"
            summary = f"Best new link for {g.label(node)} ({node}) by {how}: {first}, score {result[0]['score']}."
        else:
            result = [{"source": node_ref(g, u), "target": node_ref(g, v), "score": -neg}
                      for neg, u, v in best[:shown]]
            first = f"{result[0]['source']['label']} -> {result[0]['target']['label']}" if use_direction \
                else f"{result[0]['source']['label']} - {result[0]['target']['label']}"
            summary = f"Most likely new link by {how}: {first}, score {result[0]['score']}."
        summary += (f" Showing {len(result)} of {counter[0]} unlinked pairs scored.{way}"
                    f" Edge weights are ignored.")
        return ok(result, summary)

    shown = len(best)
    out = build(shown)
    while shown > 1 and len(json.dumps(out, sort_keys=True).encode("utf-8")) > MAX_OUTPUT_BYTES - 500:
        shown -= 1
        out = build(shown)
    return out

