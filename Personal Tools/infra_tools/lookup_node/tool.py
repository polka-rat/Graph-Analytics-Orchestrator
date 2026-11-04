from difflib import SequenceMatcher

from graphkit.contract import check_top_k, error, get_graph, node_ref, ok

THRESHOLD = 0.7


def _searchable_attributes(g):
    """String attributes that mostly identify a node (e.g. city), not ones shared by many (e.g. country)."""
    nodes = g.nodes()
    attrs = [k for k, v in g.node_attrs(nodes[0]).items() if k != "label" and isinstance(v, str)] if nodes else []
    return [k for k in attrs if len({g.node_attrs(n)[k] for n in nodes}) > 0.5 * len(nodes)]


def _score(query, text):
    text = text.lower()
    if query == text:
        return 1.0
    words = text.replace("(", " ").replace(")", " ").replace(",", " ").split()
    if query in words or query in text:
        return 0.9
    n = len(query.split())
    windows = [" ".join(words[i:i + n]) for i in range(max(1, len(words) - n + 1))]
    best = max(SequenceMatcher(None, query, w).ratio() for w in windows)
    return max(best * 0.85, SequenceMatcher(None, query, text).ratio() * 0.85)


def run(store, graph_id, name=None, top_k=5, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}.")
    if not isinstance(name, str) or not name.strip():
        return error("Give the name to look for in 'name', e.g. name='Chennai'.")
    k, err = check_top_k(top_k)
    if err:
        return err
    query = name.strip().lower()
    attrs = _searchable_attributes(g)
    matches = []
    for node in g.nodes():
        a = g.node_attrs(node)
        candidates = [("id", node), ("label", a["label"])] + [(k2, a[k2]) for k2 in attrs]
        best = max(((_score(query, str(text)), field) for field, text in candidates), key=lambda x: x[0])
        if best[0] >= THRESHOLD:
            matches.append((best[0], node, best[1]))
    matches.sort(key=lambda m: (-m[0], m[1]))
    result = [node_ref(g, node, score=round(s, 3), matched_on=field) for s, node, field in matches[:k]]
    if not result:
        return ok([], f"No node in '{graph_id}' matches '{name}'. It may not be in this graph; "
                      f"try another spelling or check list_graphs.")
    top = result[0]
    return ok(result, f"Best match for '{name}' is {top['label']} (id {top['id']}, score {top['score']}); "
                      f"{len(result)} match(es) returned.")
