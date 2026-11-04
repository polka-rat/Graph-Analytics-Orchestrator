from graphkit.contract import error, ok


def run(store, include_subgraphs=False, **params):
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. list_graphs takes only include_subgraphs.")
    graphs = [g for g in store.list_graphs() if include_subgraphs or g["parent_id"] is None]
    names = ", ".join(g["graph_id"] for g in graphs)
    return ok(graphs, f"{len(graphs)} graphs are available: {names}.")
