from graphkit.contract import check_node, error, get_graph, node_ref, ok


def run(store, graph_id, node_id=None, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}.")
    err = check_node(g, node_id, "node_id")
    if err:
        return err
    attrs = {k: v for k, v in g.node_attrs(node_id).items() if k != "label"}
    described = ", ".join(f"{k}={v}" for k, v in attrs.items()) or "no other attributes"
    return ok(node_ref(g, node_id, attributes=attrs), f"{g.label(node_id)} ({node_id}): {described}.")
