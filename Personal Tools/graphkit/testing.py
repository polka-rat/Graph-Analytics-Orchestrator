"""Helpers for tests. NetworkX is allowed in tests (as a reference), never in tool.py.

    from graphkit.testing import store, to_networkx, load
    tool = load(__file__)            # the tool in the folder above this tests/ folder
    out = tool.run(store(), graph_id="karate", top_k=5)
    G = to_networkx(store().get("karate"))
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from .graph import Graph
from .loader import Tool, load_tool
from .store import GraphStore


@lru_cache(maxsize=1)
def store() -> GraphStore:
    return GraphStore()


def load(test_file: str) -> Tool:
    """Load the tool whose folder contains this tests/ folder."""
    return load_tool(Path(test_file).resolve().parent.parent)


def to_networkx(graph: Graph):
    import networkx as nx

    G = nx.DiGraph() if graph.directed else nx.Graph()
    for n in graph.nodes():
        G.add_node(n, **dict(graph.node_attrs(n)))
    for u, v, w in graph.edges():
        G.add_edge(u, v, weight=w, **dict(graph.edge_attrs(u, v)))
    return G
