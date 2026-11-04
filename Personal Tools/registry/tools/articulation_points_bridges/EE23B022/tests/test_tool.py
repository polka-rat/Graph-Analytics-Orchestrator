"""Tests for the articulation-points-and-bridges tool."""

import networkx as nx

from graphkit.testing import load, store, to_networkx


tool = load(__file__)


def bridge_ids(output):
    return {
        tuple(sorted((bridge["source"]["id"], bridge["target"]["id"])))
        for bridge in output["result"]["bridges"]
    }


def test_matches_networkx_on_karate():
    output = tool.run(store(), graph_id="karate", top_k=100)
    graph = to_networkx(store().get("karate"))

    assert output["status"] == "ok"
    assert {node["id"] for node in output["result"]["articulation_points"]} == set(nx.articulation_points(graph))
    assert bridge_ids(output) == {tuple(sorted(edge)) for edge in nx.bridges(graph)}


def test_weighted_undirected_graph_matches_networkx():
    output = tool.run(store(), graph_id="lesmis", top_k=100)
    graph = to_networkx(store().get("lesmis"))

    assert output["status"] == "ok"
    assert {node["id"] for node in output["result"]["articulation_points"]} == set(nx.articulation_points(graph))
    assert bridge_ids(output) == {tuple(sorted(edge)) for edge in nx.bridges(graph)}


def test_directed_graph_uses_its_underlying_undirected_structure():
    output = tool.run(store(), graph_id="courses", top_k=100)
    graph = to_networkx(store().get("courses")).to_undirected()

    assert output["status"] == "ok"
    assert {node["id"] for node in output["result"]["articulation_points"]} == set(nx.articulation_points(graph))
    assert bridge_ids(output) == {tuple(sorted(edge)) for edge in nx.bridges(graph)}


def test_top_k_truncates_lists_but_preserves_totals():
    full = tool.run(store(), graph_id="courses", top_k=100)
    limited = tool.run(store(), graph_id="courses", top_k=1)

    assert limited["status"] == "ok"
    assert len(limited["result"]["articulation_points"]) <= 1
    assert len(limited["result"]["bridges"]) <= 1
    assert limited["result"]["total_articulation_points"] == full["result"]["total_articulation_points"]
    assert limited["result"]["total_bridges"] == full["result"]["total_bridges"]
    assert limited["result"]["truncated"] is True


def test_unknown_graph_is_an_error():
    output = tool.run(store(), graph_id="no_such_graph")

    assert output["status"] == "error"


def test_invalid_top_k_and_unknown_parameter_are_errors():
    assert tool.run(store(), graph_id="karate", top_k=0)["status"] == "error"
    assert tool.run(store(), graph_id="karate", extra=True)["status"] == "error"
