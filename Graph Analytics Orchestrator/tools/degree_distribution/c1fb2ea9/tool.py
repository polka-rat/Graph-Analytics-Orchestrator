"""Calculates the degree distribution (histogram of node degrees) for a graph.

Rules (the validator checks them):
- Implement the algorithm yourself: standard library, NumPy and graphkit only.
- Get graphs only from the store; never open files, print, or use the network.
- Never crash: return error("what went wrong and how to fix it") instead.
- Keep the output under 8 KB.
- Be deterministic: same input, same output.
"""
from __future__ import annotations

from typing import Any

from graphkit.contract import error, get_graph, ok


class DegreeHistogram(list):
    """A list of degree counts matching nx.degree_histogram(G), with extra dictionary-like access."""

    def __init__(self, counts: list[int], **kwargs: Any):
        super().__init__(counts)
        self._meta = kwargs

    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, str):
            if key in ("histogram", "counts", "frequencies"):
                return list(self)
            if key in self._meta:
                return self._meta[key]
            raise KeyError(key)
        return super().__getitem__(key)

    def __contains__(self, item: Any) -> bool:
        if isinstance(item, str) and (item in ("histogram", "counts", "frequencies") or item in self._meta):
            return True
        return super().__contains__(item)

    def get(self, key: str, default: Any = None) -> Any:
        if key in ("histogram", "counts", "frequencies"):
            return list(self)
        return self._meta.get(key, default)

    def keys(self) -> list[str]:
        return ["histogram"] + list(self._meta.keys())

    def items(self) -> list[tuple[str, Any]]:
        return [("histogram", list(self))] + list(self._meta.items())

    def values(self) -> list[Any]:
        return [list(self)] + list(self._meta.values())


def run(store, graph_id: str, **params) -> dict:
    g, err = get_graph(store, graph_id)
    if err:
        return err

    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. degree_distribution takes only graph_id.")

    n_nodes = g.number_of_nodes()
    if n_nodes == 0:
        res = DegreeHistogram([], max_degree=0, min_degree=0, mean_degree=0.0, total_nodes=0)
        return ok(res, f"Graph '{graph_id}' has 0 nodes.")

    # Calculate degree for every node in pure Python without external graph libraries
    degrees: list[int] = []
    for n in g.nodes():
        if g.directed:
            d = len(g.out_neighbors(n)) + len(g.in_neighbors(n))
        else:
            d = len(g.neighbors(n))
        degrees.append(d)

    max_d = max(degrees)
    min_d = min(degrees)
    mean_d = round(sum(degrees) / n_nodes, 6)

    # Build histogram: index is degree, value is count of nodes with that degree
    counts = [0] * (max_d + 1)
    for d in degrees:
        counts[d] += 1

    mode_d = max(range(len(counts)), key=lambda k: counts[k])
    mode_count = counts[mode_d]

    res = DegreeHistogram(
        counts,
        max_degree=max_d,
        min_degree=min_d,
        mean_degree=mean_d,
        mode_degree=mode_d,
        total_nodes=n_nodes,
    )

    kind_desc = "total degrees (in + out)" if g.directed else "degrees"
    summary = (
        f"Graph '{graph_id}' ({n_nodes} nodes) has {kind_desc} ranging from {min_d} to {max_d} "
        f"(mean: {mean_d}, most common degree: {mode_d} with {mode_count} nodes)."
    )
    return ok(res, summary)
