"""Tests for Part A's node_degree. Run from the repository root:  python -m pytest tests/bootcamp"""
from pathlib import Path

import networkx as nx

from graphkit import load_tool
from graphkit.testing import store, to_networkx
from graphkit.validate import validate

TOOL_DIR = Path(__file__).resolve().parents[2] / "bootcamp" / "node_degree"
tool = load_tool(TOOL_DIR)


def test_passes_the_validator():
    report = validate(TOOL_DIR)
    assert not report.errors, "validator errors:\n" + "\n".join(report.errors)


def test_undirected_degree_matches_networkx():
    G = to_networkx(store().get("karate"))
    for node in G:
        out = tool.run(store(), graph_id="karate", node=node)
        assert out["status"] == "ok"
        assert out["result"]["degree"] == G.degree(node)


def test_directed_in_and_out_degree_match_networkx():
    G = to_networkx(store().get("airports"))
    for node in ["MAA", "LIS", "DEL", "ATL", "FRA"]:
        r = tool.run(store(), graph_id="airports", node=node)["result"]
        assert r["out_degree"] == G.out_degree(node)
        assert r["in_degree"] == G.in_degree(node)
        assert r["degree"] == G.out_degree(node) + G.in_degree(node)


def test_result_is_a_node_reference():
    r = tool.run(store(), graph_id="airports", node="MAA")["result"]
    assert r["id"] == "MAA" and r["label"] == "Chennai International Airport"


def test_summary_is_a_sentence():
    out = tool.run(store(), graph_id="lesmis", node="c74")
    assert isinstance(out["summary"], str) and len(out["summary"]) > 10


def test_unknown_node_is_an_error_not_a_crash():
    out = tool.run(store(), graph_id="airports", node="Chennai")
    assert out["status"] == "error"
    assert "lookup_node" in out["error"]


def test_unknown_graph_is_an_error():
    assert tool.run(store(), graph_id="no_such_graph", node="m1")["status"] == "error"


def test_unknown_parameter_is_an_error():
    assert tool.run(store(), graph_id="karate", node="m1", weighted=True)["status"] == "error"
