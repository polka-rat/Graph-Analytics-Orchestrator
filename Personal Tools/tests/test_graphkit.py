"""Checks that the provided infrastructure works. Run:  python -m pytest tests"""
import json
from pathlib import Path

import pytest

from graphkit import GraphStore, discover
from graphkit.testing import to_networkx
from graphkit.validate import validate

ROOT = Path(__file__).resolve().parents[1]
INDEX = json.loads((ROOT / "data" / "graphs.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("graph_id", sorted(INDEX))
def test_every_dataset_loads(graph_id):
    g = GraphStore().get(graph_id)
    assert g.number_of_nodes() > 0 and g.number_of_edges() > 0
    assert g.directed == INDEX[graph_id]["directed"]
    G = to_networkx(g)
    assert G.number_of_edges() == g.number_of_edges()


def test_subgraph_registration():
    store = GraphStore()
    sub_id = store.subgraph("karate", ["m1", "m2", "m3"], "three members")
    sub = store.get(sub_id)
    assert sub.number_of_nodes() == 3 and sub.parent_id == "karate"
    assert sub.label("m1") == "Member 1 (instructor)"


def test_edge_subgraph_registration():
    store = GraphStore()
    sub = store.get(store.edge_subgraph("airports", [("MAA", "DEL"), ("DEL", "LHR")], "a route"))
    assert sub.number_of_edges() == 2 and sub.weight("MAA", "DEL") == store.get("airports").weight("MAA", "DEL")


def test_graphs_are_read_only():
    g = GraphStore().get("karate")
    with pytest.raises(TypeError):
        g.out_neighbors("m1")["m2"] = 5.0


@pytest.mark.parametrize("tool", discover(ROOT / "infra_tools"), ids=lambda t: t.name)
def test_infra_tools_pass_the_validator(tool):
    report = validate(tool.path)
    assert not report.errors, "\n".join(report.errors)
