"""Helpers for producing output that follows the tool contract.

Every tool returns a dict with exactly these keys:

    {"status": "ok" | "error",
     "result": <JSON data, or None on error>,
     "summary": "<one or two plain sentences>",
     "result_graph_id": "<id of a registered subgraph>" or None,
     "error": None or "<what went wrong and how to fix it>"}

Use ok() and error() to build it, and node_ref() for every node you return.
"""
from __future__ import annotations

from typing import Any

from .graph import Graph
from .store import GraphNotFound, GraphStore

OUTPUT_KEYS = ("status", "result", "summary", "result_graph_id", "error")
DEFAULT_TOP_K = 10
MAX_TOP_K = 100
MAX_OUTPUT_BYTES = 8 * 1024
TIME_LIMIT_SECONDS = 30


def ok(result: Any, summary: str, result_graph_id: str | None = None) -> dict:
    """A successful result. `summary` should be readable on its own by an LLM."""
    return {"status": "ok", "result": result, "summary": summary,
            "result_graph_id": result_graph_id, "error": None}


def error(message: str) -> dict:
    """A failed call. Say what went wrong AND how to fix it."""
    return {"status": "error", "result": None, "summary": message,
            "result_graph_id": None, "error": message}


def node_ref(graph: Graph, node: str, **extra: Any) -> dict:
    """How every node appears in a result: {"id": ..., "label": ..., **extra}."""
    return {"id": node, "label": graph.label(node), **extra}


def get_graph(store: GraphStore, graph_id: str) -> tuple[Graph | None, dict | None]:
    """(graph, None) on success, or (None, error_dict) if the graph does not exist.

        g, err = get_graph(store, graph_id)
        if err:
            return err
    """
    if not isinstance(graph_id, str):
        return None, error("graph_id must be a string. Use list_graphs to see the available graphs.")
    try:
        return store.get(graph_id), None
    except GraphNotFound:
        return None, error(f"No graph with id '{graph_id}'. Use list_graphs to see the available graphs.")


def check_node(graph: Graph, node: Any, param: str = "node") -> dict | None:
    """None if `node` is a node of the graph, else an error dict."""
    if not isinstance(node, str) or not graph.has_node(node):
        return error(f"Node '{node}' (parameter '{param}') is not in graph '{graph.graph_id}'. "
                     f"Use lookup_node to find node ids.")
    return None


def check_top_k(top_k: Any) -> tuple[int | None, dict | None]:
    """(k, None) if top_k is a whole number from 1 to 100, else (None, error_dict)."""
    if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= MAX_TOP_K:
        return None, error(f"top_k must be a whole number from 1 to {MAX_TOP_K}; got {top_k!r}.")
    return top_k, None
