"""Tests for the bipartite maximum-matching tool."""

import networkx as nx

from graphkit.testing import load, store, to_networkx


tool = load(__file__)


def match_pairs(output):
    matches = output["result"]["matches"]
    return {(pair["left"]["id"], pair["right"]["id"]) for pair in matches}


def test_projects_matching_has_networkx_maximum_size():
    output = tool.run(store(), graph_id="projects", top_k=100)
    graph = to_networkx(store().get("projects"))
    students = {node for node, attrs in graph.nodes(data=True) if attrs["side"] == "student"}
    expected = nx.bipartite.maximum_matching(graph, top_nodes=students)

    assert output["status"] == "ok"
    assert output["result"]["matching_size"] == len(expected) // 2
    assert len(match_pairs(output)) == len(expected) // 2


def test_project_matches_are_valid_and_use_each_endpoint_once():
    output = tool.run(store(), graph_id="projects", top_k=100)
    graph = to_networkx(store().get("projects"))
    pairs = match_pairs(output)

    assert all(graph.has_edge(student, project) for student, project in pairs)
    assert len({student for student, _ in pairs}) == len(pairs)
    assert len({project for _, project in pairs}) == len(pairs)


def test_matches_use_generic_partition_field_names():
    output = tool.run(store(), graph_id="projects")

    assert output["status"] == "ok"
    assert {"left", "right"} == set(output["result"]["matches"][0])


def test_top_k_limits_displayed_pairs_not_matching_size():
    full = tool.run(store(), graph_id="projects", top_k=100)
    limited = tool.run(store(), graph_id="projects", top_k=1)

    assert limited["status"] == "ok"
    assert len(limited["result"]["matches"]) == 1
    assert limited["result"]["matching_size"] == full["result"]["matching_size"]
    assert limited["result"]["truncated"] is True


def test_non_bipartite_graph_is_an_error():
    output = tool.run(store(), graph_id="karate")

    assert output["status"] == "error"
    assert "not bipartite" in output["error"].lower()


def test_unknown_graph_invalid_top_k_and_unknown_parameter_are_errors():
    assert tool.run(store(), graph_id="no_such_graph")["status"] == "error"
    assert tool.run(store(), graph_id="projects", top_k=0)["status"] == "error"
    assert tool.run(store(), graph_id="projects", extra=True)["status"] == "error"
