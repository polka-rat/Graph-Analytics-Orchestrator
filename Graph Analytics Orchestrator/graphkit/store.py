"""The graph store: the only way tools get graphs.

    store = GraphStore()            # loads the datasets in data/
    g = store.get("airports")       # a read-only Graph
    sub_id = store.subgraph("airports", ["MAA", "DEL", "BOM"], "Three Indian airports")
    store.get(sub_id)               # the new subgraph, usable by any tool

Datasets are loaded lazily on first use. Subgraphs registered by tools live
in memory for as long as the store object does.
"""
from __future__ import annotations

import csv
import itertools
import json
from pathlib import Path
from typing import Iterable

from .graph import Graph

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_CASTS = {"str": str, "int": int, "float": float}


class GraphNotFound(KeyError):
    pass


class GraphStore:
    def __init__(self, data_dir: str | Path | None = None):
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
        self._meta: dict[str, dict] = json.loads((self.data_dir / "graphs.json").read_text(encoding="utf-8"))
        self._graphs: dict[str, Graph] = {}
        self._counter = itertools.count(1)

    # ----- reading -----
    def list_graphs(self) -> list[dict]:
        """Metadata for every graph: datasets first, then registered subgraphs."""
        out = []
        for gid in list(self._meta) + [g for g in self._graphs if g not in self._meta]:
            g = self.get(gid)
            out.append({"graph_id": gid, "description": g.description, "directed": g.directed,
                        "weighted": g.weighted, "nodes": g.number_of_nodes(), "edges": g.number_of_edges(),
                        "parent_id": g.parent_id})
        return out

    def has_graph(self, graph_id: str) -> bool:
        return graph_id in self._graphs or graph_id in self._meta

    def get(self, graph_id: str) -> Graph:
        """Return the graph with this id. Raises GraphNotFound if there is none."""
        if graph_id not in self._graphs:
            if graph_id not in self._meta:
                raise GraphNotFound(f"No graph with id '{graph_id}'. Use list_graphs to see the available graphs.")
            self._graphs[graph_id] = self._load(graph_id)
        return self._graphs[graph_id]

    def _load(self, graph_id: str) -> Graph:
        meta = self._meta[graph_id]
        g = Graph(graph_id, directed=meta["directed"], weighted=meta["weighted"], description=meta["description"])
        gdir = self.data_dir / graph_id
        ncast = {k: _CASTS[t] for k, t in meta.get("node_attributes", {}).items()}
        ecast = {k: _CASTS[t] for k, t in meta.get("edge_attributes", {}).items()}
        with open(gdir / "nodes.csv", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                g._add_node(row["id"], row["label"], **{k: c(row[k]) for k, c in ncast.items()})
        with open(gdir / "edges.csv", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                weight = float(row["weight"]) if meta["weighted"] else 1.0
                g._add_edge(row["source"], row["target"], weight, **{k: c(row[k]) for k, c in ecast.items()})
        return g

    # ----- registering results -----
    def subgraph(self, graph_id: str, nodes: Iterable[str], description: str) -> str:
        """Register the subgraph induced by `nodes` (those nodes and every edge among them).

        Returns the new graph's id, e.g. 'airports~3'. Use it as result_graph_id.
        """
        parent = self.get(graph_id)
        keep = list(dict.fromkeys(nodes))
        missing = [n for n in keep if not parent.has_node(n)]
        if missing:
            raise ValueError(f"nodes not in '{graph_id}': {missing[:5]}")
        keep_set = set(keep)
        g = self._new_child(parent, description)
        for n in keep:
            g._add_node(n, **dict(parent.node_attrs(n)))
        for u, v, w in parent.edges():
            if u in keep_set and v in keep_set:
                g._add_edge(u, v, w, **dict(parent.edge_attrs(u, v)))
        return self._register(g)

    def edge_subgraph(self, graph_id: str, edges: Iterable[tuple[str, str]], description: str) -> str:
        """Register the subgraph made of the given edges (u, v) and their endpoints.

        Useful for results such as a spanning tree or a path. Returns the new graph's id.
        """
        parent = self.get(graph_id)
        edge_list = list(edges)
        g = self._new_child(parent, description)
        for u, v in edge_list:
            if not parent.has_edge(u, v):
                raise ValueError(f"no edge {u!r}->{v!r} in '{graph_id}'")
            for n in (u, v):
                if not g.has_node(n):
                    g._add_node(n, **dict(parent.node_attrs(n)))
            if not g.has_edge(u, v):
                g._add_edge(u, v, parent.weight(u, v), **dict(parent.edge_attrs(u, v)))
        return self._register(g)

    def _new_child(self, parent: Graph, description: str) -> Graph:
        root = parent.graph_id.split("~")[0]
        gid = f"{root}~{next(self._counter)}"
        return Graph(gid, directed=parent.directed, weighted=parent.weighted,
                     description=description, parent_id=parent.graph_id)

    def _register(self, g: Graph) -> str:
        self._graphs[g.graph_id] = g
        return g.graph_id
