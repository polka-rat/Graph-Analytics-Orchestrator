"""Tests for your tool. Run from the repository root:  python -m pytest registry/tools/<tool>/<you>/tests

NetworkX is allowed HERE as a reference implementation, never in tool.py.
Write at least five tests. These five are a starting point: adapt them to your tool.
"""
from graphkit.testing import load, store, to_networkx

tool = load(__file__)


def test_matches_networkx_on_karate():
    import networkx as nx

    out = tool.run(store(), graph_id="karate", top_k=5)
    assert out["status"] == "ok"
    G = to_networkx(store().get("karate"))
    expected = nx.degree_centrality(G)  # TODO: replace with the NetworkX function for your algorithm
    for entry in out["result"]:
        assert abs(entry["score"] - expected[entry["id"]]) < 1e-6


def test_unknown_graph_is_an_error():
    out = tool.run(store(), graph_id="no_such_graph")
    assert out["status"] == "error"


def test_bad_top_k_is_an_error():
    assert tool.run(store(), graph_id="karate", top_k=0)["status"] == "error"
    assert tool.run(store(), graph_id="karate", top_k=500)["status"] == "error"


def test_respects_top_k():
    out = tool.run(store(), graph_id="airports", top_k=3)
    assert len(out["result"]) == 3


def test_is_deterministic():
    assert tool.run(store(), graph_id="lesmis", top_k=5) == tool.run(store(), graph_id="lesmis", top_k=5)
