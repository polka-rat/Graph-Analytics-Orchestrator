"""The Graph class that every tool works with.

Graphs are read-only. Get one from the store (``store.get(graph_id)``);
never build or load graphs yourself inside a tool.

Node ids are strings. Every node has a human-readable label.
Edge weights are floats; an unweighted graph reports weight 1.0 everywhere.
"""
from __future__ import annotations

from types import MappingProxyType
from typing import Iterator, Mapping


class Graph:
    def __init__(self, graph_id: str, *, directed: bool, weighted: bool, description: str = "",
                 parent_id: str | None = None):
        self.graph_id = graph_id
        self.directed = directed
        self.weighted = weighted
        self.description = description
        self.parent_id = parent_id  # set for subgraphs registered by tools
        self._attrs: dict[str, dict] = {}            # node -> attributes (always has "label")
        self._out: dict[str, dict[str, float]] = {}  # node -> {neighbour: weight}
        self._in: dict[str, dict[str, float]] = {}   # same object as _out for undirected graphs
        self._edge_attrs: dict[tuple[str, str], dict] = {}
        self._n_edges = 0

    # ----- construction (used by the store; tools should not call these) -----
    def _add_node(self, node: str, label: str, **attrs) -> None:
        if node in self._attrs:
            raise ValueError(f"duplicate node {node!r}")
        self._attrs[node] = {"label": label, **attrs}
        self._out[node] = {}
        self._in[node] = self._out[node] if not self.directed else {}

    def _add_edge(self, u: str, v: str, weight: float = 1.0, **attrs) -> None:
        if u not in self._attrs or v not in self._attrs:
            raise ValueError(f"edge {u!r}->{v!r} uses an unknown node")
        if v in self._out[u]:
            raise ValueError(f"duplicate edge {u!r}->{v!r}")
        self._out[u][v] = float(weight)
        self._in[v][u] = float(weight)
        if attrs:
            self._edge_attrs[self._key(u, v)] = dict(attrs)
        self._n_edges += 1

    def _key(self, u: str, v: str) -> tuple[str, str]:
        return (u, v) if self.directed or u <= v else (v, u)

    # ----- nodes -----
    def nodes(self) -> list[str]:
        """All node ids, in a fixed order."""
        return list(self._attrs)

    def has_node(self, node: str) -> bool:
        return node in self._attrs

    def number_of_nodes(self) -> int:
        return len(self._attrs)

    def label(self, node: str) -> str:
        """Human-readable name of a node. Raises KeyError for an unknown node."""
        return self._attrs[node]["label"]

    def node_attrs(self, node: str) -> Mapping[str, object]:
        """All attributes of a node, including 'label'."""
        return MappingProxyType(self._attrs[node])

    # ----- edges -----
    def number_of_edges(self) -> int:
        """Number of edges (an undirected edge counts once)."""
        return self._n_edges

    def out_neighbors(self, node: str) -> Mapping[str, float]:
        """{neighbour: weight} for edges leaving node. For undirected graphs: all neighbours."""
        return MappingProxyType(self._out[node])

    def in_neighbors(self, node: str) -> Mapping[str, float]:
        """{neighbour: weight} for edges entering node. For undirected graphs: all neighbours."""
        return MappingProxyType(self._in[node])

    def neighbors(self, node: str) -> Mapping[str, float]:
        """Same as out_neighbors (as in NetworkX)."""
        return self.out_neighbors(node)

    def undirected_neighbors(self, node: str) -> Mapping[str, float]:
        """Neighbours ignoring direction. For a pair joined both ways, the smaller weight is kept."""
        if not self.directed:
            return self.out_neighbors(node)
        merged = dict(self._in[node])
        for v, w in self._out[node].items():
            merged[v] = min(w, merged.get(v, w))
        return MappingProxyType(merged)

    def has_edge(self, u: str, v: str) -> bool:
        return u in self._out and v in self._out[u]

    def weight(self, u: str, v: str) -> float | None:
        """Weight of edge u->v, or None if there is no such edge."""
        return self._out.get(u, {}).get(v)

    def edge_attrs(self, u: str, v: str) -> Mapping[str, object]:
        """Extra attributes of edge u->v (for example 'airlines'), not including weight."""
        if not self.has_edge(u, v):
            raise KeyError(f"no edge {u!r}->{v!r}")
        return MappingProxyType(self._edge_attrs.get(self._key(u, v), {}))

    def edges(self) -> Iterator[tuple[str, str, float]]:
        """Yield (u, v, weight). Each undirected edge is yielded once."""
        seen: set[tuple[str, str]] = set()
        for u, nbrs in self._out.items():
            for v, w in nbrs.items():
                if not self.directed:
                    k = self._key(u, v)
                    if k in seen:
                        continue
                    seen.add(k)
                yield u, v, w

    def __repr__(self) -> str:
        kind = "directed" if self.directed else "undirected"
        return f"<Graph {self.graph_id!r}: {kind}, {self.number_of_nodes()} nodes, {self.number_of_edges()} edges>"
