"""Cache behavior, invalidation, and validation-semantic checks."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from graphkit.loader import discover, find_tool_dirs, load_manifest, load_tool
from graphkit.store import GraphStore
from graphkit.validate import validate
from graphkit.validation_cache import ValidationCache
from orchestrator.curator import ToolCurator
from orchestrator.planner import Planner

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION = (
    "Lists the graphs you can analyse, with each graph's id, a description of "
    "what its nodes and edges mean, whether it is directed or weighted, and its "
    "node and edge counts. Call this first when you do not know which graph a question is about."
)


def _list_graphs_source(warn: bool) -> str:
    warning = "    if False:\n        print('debug')\n" if warn else ""
    return (
        "from graphkit.contract import error, ok\n"
        "\n"
        "\n"
        "def run(store, include_subgraphs=False, **params):\n"
        f"{warning}"
        "    if params:\n"
        "        return error('Unknown parameter(s): ' + ', '.join(params))\n"
        "    graphs = [item for item in store.list_graphs() if include_subgraphs or item['parent_id'] is None]\n"
        "    names = ', '.join(item['graph_id'] for item in graphs)\n"
        "    return ok(graphs, f'{len(graphs)} graphs are available: {names}.')\n"
    )


def write_list_graphs(folder: Path, implementation_id: str, author: str, warn: bool = False) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    manifest = {
        "name": "list_graphs",
        "implementation_id": implementation_id,
        "author": author,
        "tier": "infra",
        "category": "infrastructure",
        "description": DESCRIPTION,
        "parameters": {
            "type": "object",
            "properties": {
                "include_subgraphs": {
                    "type": "boolean",
                    "description": "Also list subgraphs created by earlier tool calls.",
                    "default": False,
                }
            },
            "required": [],
        },
        "examples": [{}],
    }
    (folder / "tool.json").write_text(json.dumps(manifest), encoding="utf-8")
    (folder / "tool.py").write_text(_list_graphs_source(warn), encoding="utf-8")


def write_invalid(folder: Path, name: str, implementation_id: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "tool.json").write_text(
        json.dumps({"name": name, "implementation_id": implementation_id}),
        encoding="utf-8",
    )
    (folder / "tool.py").write_text("def run(store, graph_id=None, **params):\n    return {}\n", encoding="utf-8")


def make_curator(root: Path, infra: Path, registry: Path, **kwargs) -> ToolCurator:
    return ToolCurator(
        infra,
        registry,
        project_root=kwargs.pop("project_root", root),
        cache_dir=kwargs.pop("cache_dir", root / "cache"),
        **kwargs,
    )


def records_of(curator: ToolCurator):
    return [
        (record.implementation_id, record.selected, list(record.errors), list(record.warnings))
        for record in curator.records
    ]


def write_tiny_data(root: Path) -> None:
    data = root / "data"
    (data / "karate").mkdir(parents=True)
    (data / "graphs.json").write_text('{"karate": {}}\n', encoding="utf-8")
    (data / "karate" / "nodes.csv").write_text("id,label\n", encoding="utf-8")
    (data / "karate" / "edges.csv").write_text("source,target\n", encoding="utf-8")


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, allow_nan=False)


def test_discover_skips_template_and_does_not_import_while_scanning(tmp_path: Path) -> None:
    template = tmp_path / "template"
    template.mkdir()
    (template / "tool.json").write_text("{}", encoding="utf-8")
    (template / "tool.py").write_text("def run(store):\n    return {}\n", encoding="utf-8")
    real = tmp_path / "real"
    real.mkdir()
    (real / "tool.json").write_text(json.dumps({"name": "list_graphs", "implementation_id": "list_graphs.real"}), encoding="utf-8")
    (real / "tool.py").write_text("def run(store, **params):\n    return {'ok': True}\n", encoding="utf-8")

    assert find_tool_dirs(tmp_path) == [real]
    assert find_tool_dirs(tmp_path / "missing") == []
    loaded = discover(tmp_path)
    assert [tool.path for tool in loaded] == [real.resolve()]


def test_uncached_path_does_not_write_cache_and_matches_cached_records(tmp_path: Path) -> None:
    infra = tmp_path / "infra"
    registry = tmp_path / "registry"
    write_invalid(infra / "a", "list_graphs", "list_graphs.a")
    write_invalid(registry / "degree_centrality" / "b", "degree_centrality", "degree_centrality.b")
    cache_dir = tmp_path / "cache"

    raw = make_curator(tmp_path, infra, registry)
    raw_tools = raw.curate(use_cache=False)
    assert raw_tools == {}
    assert not cache_dir.exists()

    cold = make_curator(tmp_path, infra, registry)
    cold.curate(use_cache=True)
    warm = make_curator(tmp_path, infra, registry)
    warm.curate(use_cache=True)

    assert records_of(raw) == records_of(cold) == records_of(warm)
    assert cold.validate_calls == 2
    assert warm.validate_calls == 0
    assert warm.import_calls == 0
    assert warm.cache is not None
    assert warm.cache.timings["tool_bytes_read"] == 0


def test_editing_one_tool_revalidates_only_that_folder(tmp_path: Path, monkeypatch) -> None:
    infra = tmp_path / "infra" / "a"
    other = tmp_path / "registry" / "b"
    write_invalid(infra, "list_graphs", "list_graphs.a")
    write_invalid(other, "degree_centrality", "degree_centrality.b")
    seen: list[Path] = []
    original = validate

    def wrapped(folder):
        seen.append(Path(folder).resolve())
        return original(folder)

    monkeypatch.setattr("orchestrator.curator.validate", wrapped)
    curator = make_curator(tmp_path, tmp_path / "infra", tmp_path / "registry")
    curator.curate()
    seen.clear()
    (other / "tool.py").write_text(
        "def run(store, graph_id=None, **params):\n    return {'changed': True}\n",
        encoding="utf-8",
    )
    again = make_curator(tmp_path, tmp_path / "infra", tmp_path / "registry")
    again.curate()
    assert seen == [other.resolve()]
    assert again.validate_calls == 1


def test_same_bytes_mtime_change_keeps_the_report(tmp_path: Path) -> None:
    folder = tmp_path / "infra" / "a"
    write_invalid(folder, "list_graphs", "list_graphs.a")
    first = make_curator(tmp_path, tmp_path / "infra", tmp_path / "empty")
    first.curate()
    entry = next((tmp_path / "cache" / "tools").glob("*.json"))
    before = json.loads(entry.read_text(encoding="utf-8"))
    tool_py = folder / "tool.py"
    stat = tool_py.stat()
    os.utime(tool_py, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))

    second = make_curator(tmp_path, tmp_path / "infra", tmp_path / "empty")
    second.curate()
    after = json.loads(entry.read_text(encoding="utf-8"))
    assert second.validate_calls == 0
    assert after["errors"] == before["errors"]
    assert after["warnings"] == before["warnings"]
    new_mtime = next(item["mtime_ns"] for item in after["stats"] if item["path"] == "tool.py")
    old_mtime = next(item["mtime_ns"] for item in before["stats"] if item["path"] == "tool.py")
    assert new_mtime != old_mtime
    assert new_mtime == tool_py.stat().st_mtime_ns


def test_cache_version_bump_misses(tmp_path: Path) -> None:
    write_invalid(tmp_path / "infra" / "a", "list_graphs", "list_graphs.a")
    make_curator(tmp_path, tmp_path / "infra", tmp_path / "empty", cache_version=1).curate()
    bumped = make_curator(tmp_path, tmp_path / "infra", tmp_path / "empty", cache_version=2)
    bumped.curate()
    assert bumped.validate_calls == 1


def test_truncated_cache_file_is_replaced(tmp_path: Path) -> None:
    write_invalid(tmp_path / "infra" / "a", "list_graphs", "list_graphs.a")
    make_curator(tmp_path, tmp_path / "infra", tmp_path / "empty").curate()
    entry = next((tmp_path / "cache" / "tools").glob("*.json"))
    entry.write_text("{", encoding="utf-8")
    again = make_curator(tmp_path, tmp_path / "infra", tmp_path / "empty")
    again.curate()
    assert again.validate_calls == 1
    restored = json.loads(entry.read_text(encoding="utf-8"))
    assert restored["implementation_id"] == "list_graphs.a"
    assert restored["errors"]


def test_dataset_change_misses_and_warm_stat_does_not_read(tmp_path: Path) -> None:
    write_tiny_data(tmp_path)
    write_invalid(tmp_path / "infra" / "a", "list_graphs", "list_graphs.a")
    cold = ValidationCache(tmp_path, cache_dir=tmp_path / "fingerprints")
    digest = cold.fingerprint_dataset()
    assert cold.dataset_mode == "hash"
    assert cold.dataset_hashed_paths == ["graphs.json", "karate/edges.csv", "karate/nodes.csv"]

    warm = ValidationCache(tmp_path, cache_dir=tmp_path / "fingerprints")

    def forbid(path, key):
        raise AssertionError(f"read {path} ({key})")

    warm._read_bytes = forbid
    assert warm.fingerprint_dataset() == digest
    assert warm.dataset_mode == "stat"
    assert warm.timings["dataset_bytes_read"] == 0

    graphs = tmp_path / "data" / "graphs.json"
    original = graphs.read_bytes()
    stat = graphs.stat()
    os.utime(graphs, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
    touched = ValidationCache(tmp_path, cache_dir=tmp_path / "fingerprints")
    assert touched.fingerprint_dataset() == digest
    assert touched.dataset_hashed_paths == ["graphs.json"]

    graphs.write_bytes(original + b" \n")
    changed = ValidationCache(tmp_path, cache_dir=tmp_path / "fingerprints")
    assert changed.fingerprint_dataset() != digest

    curator = make_curator(tmp_path, tmp_path / "infra", tmp_path / "empty")
    curator.curate()
    (tmp_path / "data" / "karate" / "nodes.csv").write_text("id,label\nx,X\n", encoding="utf-8")
    rerun = make_curator(tmp_path, tmp_path / "infra", tmp_path / "empty")
    rerun.curate()
    assert rerun.validate_calls == 1


def test_cache_stores_the_report_validate_returned(tmp_path: Path, monkeypatch) -> None:
    write_invalid(tmp_path / "infra" / "a", "list_graphs", "list_graphs.kept")
    seen = {}
    original = validate

    def wrapped(folder):
        report = original(folder)
        seen["errors"] = list(report.errors)
        seen["warnings"] = list(report.warnings)
        return report

    monkeypatch.setattr("orchestrator.curator.validate", wrapped)
    curator = make_curator(tmp_path, tmp_path / "infra", tmp_path / "empty")
    curator.curate()
    stored = json.loads(next((tmp_path / "cache" / "tools").glob("*.json")).read_text(encoding="utf-8"))
    assert stored["errors"] == seen["errors"]
    assert stored["warnings"] == seen["warnings"]


def test_cached_selection_matches_uncached_for_passing_tools(tmp_path: Path) -> None:
    infra = tmp_path / "infra"
    # The warning-bearing implementation sorts first by id, so selection
    # proves the warning count is applied before the id tie-break.
    write_list_graphs(infra / "noisy", "list_graphs.a", "a", warn=True)
    write_list_graphs(infra / "clean", "list_graphs.b", "b", warn=False)
    registry = tmp_path / "registry"
    write_list_graphs(registry / "tie_b", "list_graphs.b", "b", warn=False)
    write_list_graphs(registry / "tie_a", "list_graphs.a", "a", warn=False)

    raw = make_curator(tmp_path, infra, tmp_path / "no-registry")
    selected = raw.curate(use_cache=False)
    cold = make_curator(tmp_path, infra, tmp_path / "no-registry")
    cold_selected = cold.curate(use_cache=True)
    warm = make_curator(tmp_path, infra, tmp_path / "no-registry")
    warm_selected = warm.curate(use_cache=True)

    assert selected["list_graphs"].implementation_id == "list_graphs.b"
    assert cold_selected["list_graphs"].implementation_id == "list_graphs.b"
    assert warm_selected["list_graphs"].implementation_id == "list_graphs.b"
    assert records_of(raw) == records_of(cold) == records_of(warm)
    assert warm.validate_calls == 0
    assert warm.import_calls == 1

    tie_raw = make_curator(tmp_path, tmp_path / "no-infra", registry, cache_dir=tmp_path / "tie-cache")
    tie_cached = make_curator(tmp_path, tmp_path / "no-infra", registry, cache_dir=tmp_path / "tie-cache")
    assert tie_raw.curate(use_cache=False)["list_graphs"].implementation_id == "list_graphs.a"
    assert tie_cached.curate(use_cache=True)["list_graphs"].implementation_id == "list_graphs.a"
    assert records_of(tie_raw) == records_of(tie_cached)


def test_planner_falls_back_to_tools_directory(tmp_path: Path) -> None:
    write_list_graphs(tmp_path / "infra_tools" / "list_graphs", "list_graphs.instructors", "instructors")
    write_invalid(tmp_path / "tools" / "degree_centrality" / "zzz", "degree_centrality", "degree_centrality.zzz")
    planner = Planner(tmp_path)
    assert set(planner.tools) == {"list_graphs"}
    assert planner.curation["candidates"] == 2
    assert "degree_centrality.zzz" in planner.curation["rejection_reasons"]


def test_validate_cli_does_not_read_or_write_cache(tmp_path: Path) -> None:
    folder = tmp_path / "tool"
    write_invalid(folder, "list_graphs", "list_graphs.cli")
    project_cache = ROOT / ".cache" / "tool_validation"
    before = {path.relative_to(project_cache) for path in project_cache.rglob("*")} if project_cache.exists() else set()

    report = validate(folder)
    assert report.errors

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    completed = subprocess.run(
        [sys.executable, "-m", "graphkit.validate", str(folder)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 1
    assert not (tmp_path / ".cache").exists()
    after = {path.relative_to(project_cache) for path in project_cache.rglob("*")} if project_cache.exists() else set()
    assert after == before


def test_representative_tools_keep_validation_and_behavior(tmp_path: Path) -> None:
    real_folders = [
        ROOT / "infra_tools" / "lookup_node",
        ROOT / "tools" / "degree_centrality" / "a018559c",
        ROOT / "tools" / "betweenness_centrality" / "f6f61ae0",
    ]
    infra = tmp_path / "infra" / "lookup_node"
    registry = tmp_path / "registry"
    shutil.copytree(real_folders[0], infra)
    shutil.copytree(real_folders[1], registry / "degree_centrality" / "a018559c")
    shutil.copytree(real_folders[2], registry / "betweenness_centrality" / "f6f61ae0")

    direct = {}
    for folder in real_folders:
        report = validate(folder)
        manifest = load_manifest(folder)
        direct[manifest["implementation_id"]] = report
        first = load_tool(folder)
        second = load_tool(folder)
        for example in first.manifest["examples"]:
            assert canonical(first.run(GraphStore(), **example)) == canonical(second.run(GraphStore(), **example))

    curator = make_curator(tmp_path, tmp_path / "infra", registry, project_root=ROOT, cache_dir=tmp_path / "cache")
    selected = curator.curate()
    for entry in (tmp_path / "cache" / "tools").glob("*.json"):
        stored = json.loads(entry.read_text(encoding="utf-8"))
        report = direct[stored["implementation_id"]]
        assert stored["errors"] == list(report.errors)
        assert stored["warnings"] == list(report.warnings)

    warm = make_curator(tmp_path, tmp_path / "infra", registry, project_root=ROOT, cache_dir=tmp_path / "cache")
    warmed = warm.curate()
    assert warm.validate_calls == 0
    assert {name: tool.implementation_id for name, tool in warmed.items()} == {
        name: tool.implementation_id for name, tool in selected.items()
    }
    for folder in real_folders:
        manifest = load_manifest(folder)
        if manifest["name"] not in warmed:
            continue
        original = load_tool(folder)
        chosen = warmed[manifest["name"]]
        for example in manifest["examples"]:
            assert canonical(original.run(GraphStore(), **example)) == canonical(
                chosen.run(GraphStore(), **example)
            )
