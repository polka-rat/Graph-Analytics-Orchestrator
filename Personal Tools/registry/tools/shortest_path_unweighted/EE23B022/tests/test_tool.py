"""Tests for the unweighted shortest-path tool."""

import networkx as nx

from graphkit.testing import load, store, to_networkx


tool = load(__file__)


def path_ids(output):
    return [node["id"] for node in output["result"]]


def test_matches_networkx_shortest_path_on_karate():
    source, destination = "m1", "m34"
    output = tool.run(store(), graph_id="karate", src=source, dest=destination)

    assert output["status"] == "ok"
    expected = nx.shortest_path(to_networkx(store().get("karate")), source, destination)
    actual = path_ids(output)
    assert actual[0] == source
    assert actual[-1] == destination
    assert len(actual) == len(expected)


def test_respects_direction_on_courses_graph():
    forward = tool.run(store(), graph_id="courses", src="CS101", dest="CS401")
    reverse = tool.run(store(), graph_id="courses", src="CS401", dest="CS101")

    assert forward["status"] == "ok"
    assert path_ids(forward)[0] == "CS101"
    assert path_ids(forward)[-1] == "CS401"
    assert reverse["status"] == "error"


def test_source_equal_to_destination_has_zero_length_path():
    output = tool.run(store(), graph_id="projects", src="S01", dest="S01")

    assert output["status"] == "ok"
    assert path_ids(output) == ["S01"]
    assert "0 edges" in output["summary"]


def test_weighted_graph_uses_hop_count_not_edge_weight():
    source, destination = "c74", "c19"
    output = tool.run(store(), graph_id="lesmis", src=source, dest=destination)

    assert output["status"] == "ok"
    expected = nx.shortest_path(to_networkx(store().get("lesmis")), source, destination)
    assert len(path_ids(output)) == len(expected)


def test_unknown_graph_is_an_error():
    output = tool.run(store(), graph_id="no_such_graph", src="m1", dest="m34")

    assert output["status"] == "error"


def test_unknown_node_and_unknown_parameter_are_errors():
    bad_node = tool.run(store(), graph_id="karate", src="not_a_node", dest="m34")
    bad_parameter = tool.run(store(), graph_id="karate", src="m1", dest="m34", extra=True)

    assert bad_node["status"] == "error"
    assert bad_parameter["status"] == "error"
