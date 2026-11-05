import operator

from graphkit.contract import error, get_graph, node_ref, ok

NUMERIC_OPS = {"gt": operator.gt, "gte": operator.ge, "lt": operator.lt, "lte": operator.le}
OPS = ("eq", "ne", "contains") + tuple(NUMERIC_OPS)


def _matches(actual, value, op):
    if op in NUMERIC_OPS or isinstance(actual, (int, float)):
        try:
            a, v = float(actual), float(value)
        except (TypeError, ValueError):
            return None
        if op == "eq":
            return a == v
        if op == "ne":
            return a != v
        if op == "contains":
            return None
        return NUMERIC_OPS[op](a, v)
    a, v = str(actual).lower(), str(value).lower()
    if op == "eq":
        return a == v
    if op == "ne":
        return a != v
    return v in a  # contains


def run(store, graph_id, attribute=None, value=None, op="eq", **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}.")
    if op not in OPS:
        return error(f"op must be one of {', '.join(OPS)}; got {op!r}.")
    if value is None:
        return error("Give the value to compare with in 'value'.")
    nodes = g.nodes()
    available = sorted(g.node_attrs(nodes[0]).keys()) if nodes else []
    if attribute not in available:
        return error(f"Nodes in '{graph_id}' have no attribute {attribute!r}. "
                     f"Available attributes: {', '.join(available)}.")
    selected = []
    for n in nodes:
        m = _matches(g.node_attrs(n)[attribute], value, op)
        if m is None:
            return error(f"Cannot apply op '{op}' to attribute '{attribute}' with value {value!r}: "
                         f"use a number for gt/gte/lt/lte and text for contains.")
        if m:
            selected.append(n)
    condition = f"{attribute} {op} {value}"
    if not selected:
        return ok({"count": 0, "sample": []}, f"No node in '{graph_id}' has {condition}.")
    sub_id = store.subgraph(graph_id, selected, f"Nodes of '{graph_id}' with {condition}")
    sample = [node_ref(g, n) for n in selected[:10]]
    sub = store.get(sub_id)
    return ok({"count": len(selected), "edges": sub.number_of_edges(), "sample": sample},
              f"{len(selected)} nodes of '{graph_id}' have {condition}; they form subgraph '{sub_id}' "
              f"with {sub.number_of_edges()} edges.", result_graph_id=sub_id)
