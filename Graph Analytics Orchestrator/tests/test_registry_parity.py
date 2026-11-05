"""Selection parity and measured startup cost on the real tool registry."""

from __future__ import annotations

import shutil
import time
from pathlib import Path

import graphkit.loader as loader
import graphkit.validate as validate_mod
import orchestrator.curator as curator_mod
from evaluation import evaluate, load_json
from graphkit.validation_cache import ValidationCache
from orchestrator.curator import ToolCurator
from orchestrator.planner import Planner

ROOT = Path(__file__).resolve().parents[1]


def _view(curator: ToolCurator):
    return [
        (record.implementation_id, record.selected, list(record.errors), list(record.warnings))
        for record in curator.records
    ]


def _selected(tools):
    return {name: tool.implementation_id for name, tool in sorted(tools.items())}


def test_real_registry_cache_matches_uncached_and_reports_timings() -> None:
    """Cold and warm planner runs must select the same implementations.

    The printed MEASUREMENT lines are the timed startup costs for this machine.
    """
    cache_dir = ROOT / ".cache" / "tool_validation"
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
    fingerprint_dir = ROOT / ".cache" / "fingerprint_bench"
    if fingerprint_dir.exists():
        shutil.rmtree(fingerprint_dir)

    cold_fp = ValidationCache(ROOT, cache_dir=fingerprint_dir)
    started = time.perf_counter()
    cold_fp.fingerprint_dataset()
    cold_fp.fingerprint_code()
    dataset_hash_seconds = time.perf_counter() - started

    warm_fp = ValidationCache(ROOT, cache_dir=fingerprint_dir)

    def forbid(path, key):
        raise AssertionError(f"warm fingerprint read {path} for {key}")

    warm_fp._read_bytes = forbid
    started = time.perf_counter()
    assert warm_fp.fingerprint_dataset() == cold_fp.fingerprint_dataset()
    dataset_stat_seconds = time.perf_counter() - started
    assert warm_fp.dataset_mode == "stat"
    assert warm_fp.timings["dataset_bytes_read"] == 0
    assert warm_fp.fingerprint_code() == cold_fp.fingerprint_code()

    expected = load_json(ROOT / "public_expected.json")
    actual = load_json(ROOT / "answers_public.json")
    evaluation_before = evaluate(expected, actual)

    import_bucket = {"seconds": 0.0, "calls": 0}
    originals = {
        "loader": loader.load_tool,
        "validate": validate_mod.load_tool,
        "curator": curator_mod.load_tool,
        "curate": ToolCurator.curate,
    }
    planners: list[ToolCurator] = []

    def wrap(function):
        def timed(*args, **kwargs):
            started_call = time.perf_counter()
            try:
                return function(*args, **kwargs)
            finally:
                import_bucket["seconds"] += time.perf_counter() - started_call
                import_bucket["calls"] += 1

        return timed

    def tracing_curate(self, use_cache=True):
        planners.append(self)
        return originals["curate"](self, use_cache=use_cache)

    loader.load_tool = wrap(originals["loader"])
    validate_mod.load_tool = wrap(originals["validate"])
    curator_mod.load_tool = wrap(originals["curator"])
    ToolCurator.curate = tracing_curate
    try:
        started = time.perf_counter()
        cold_planner = Planner()
        cold_planner_seconds = time.perf_counter() - started
        cold_import_seconds = import_bucket["seconds"]
        cold_import_calls = import_bucket["calls"]

        started = time.perf_counter()
        warm_planner = Planner()
        warm_planner_seconds = time.perf_counter() - started
        warm_import_seconds = import_bucket["seconds"] - cold_import_seconds
        warm_import_calls = import_bucket["calls"] - cold_import_calls

        infra = ROOT / "infra_tools"
        registry = ROOT / "tools"
        started = time.perf_counter()
        uncached = ToolCurator(infra, registry, project_root=ROOT)
        uncached_tools = uncached.curate(use_cache=False)
        uncached_seconds = time.perf_counter() - started

        started = time.perf_counter()
        warmed = ToolCurator(infra, registry, project_root=ROOT)
        warmed_tools = warmed.curate(use_cache=True)
        warm_curate_seconds = time.perf_counter() - started
        cold_curator = planners[0]
        warm_curator = planners[1]
        cold_timings = dict(cold_curator.cache.timings)
        warm_timings = dict(warm_curator.cache.timings)
    finally:
        loader.load_tool = originals["loader"]
        validate_mod.load_tool = originals["validate"]
        curator_mod.load_tool = originals["curator"]
        ToolCurator.curate = originals["curate"]

    evaluation_after = evaluate(expected, actual)

    assert evaluation_before == evaluation_after
    assert _selected(cold_planner.tools) == _selected(warm_planner.tools)
    assert cold_planner.curation == warm_planner.curation
    assert _selected(uncached_tools) == _selected(warmed_tools) == _selected(cold_planner.tools)
    assert _view(uncached) == _view(warmed)
    assert cold_curator.validate_calls > 0
    assert warm_curator.validate_calls == 0
    assert warm_curator.cache.timings["dataset_bytes_read"] == 0
    assert warmed.validate_calls == 0
    assert warmed.cache is not None
    assert warmed.cache.dataset_mode == "stat"
    assert warmed.cache.timings["dataset_bytes_read"] == 0

    lines = [
        f"MEASUREMENT dataset_content_hash_seconds={dataset_hash_seconds:.6f}",
        f"MEASUREMENT dataset_content_hash_bytes={cold_fp.timings['dataset_bytes_read']}",
        f"MEASUREMENT dataset_stat_reuse_seconds={dataset_stat_seconds:.6f}",
        "MEASUREMENT dataset_stat_reuse_bytes_read=0",
        f"MEASUREMENT cold_planner_seconds={cold_planner_seconds:.6f}",
        f"MEASUREMENT warm_planner_seconds={warm_planner_seconds:.6f}",
        f"MEASUREMENT cold_validate_seconds={cold_curator.validate_seconds:.6f}",
        f"MEASUREMENT cold_validate_calls={cold_curator.validate_calls}",
        f"MEASUREMENT cold_winner_import_seconds={cold_curator.import_seconds:.6f}",
        f"MEASUREMENT cold_winner_import_calls={cold_curator.import_calls}",
        f"MEASUREMENT cold_load_tool_seconds={cold_import_seconds:.6f}",
        f"MEASUREMENT cold_load_tool_calls={cold_import_calls}",
        f"MEASUREMENT cold_dataset_hash_seconds={cold_timings['dataset_hash_seconds']:.6f}",
        f"MEASUREMENT cold_dataset_stat_seconds={cold_timings['dataset_stat_seconds']:.6f}",
        f"MEASUREMENT cold_dataset_bytes_read={cold_timings['dataset_bytes_read']}",
        f"MEASUREMENT cold_tool_key_seconds={cold_timings['tool_key_seconds']:.6f}",
        f"MEASUREMENT warm_validate_seconds={warm_curator.validate_seconds:.6f}",
        f"MEASUREMENT warm_load_tool_seconds={warm_import_seconds:.6f}",
        f"MEASUREMENT warm_load_tool_calls={warm_import_calls}",
        f"MEASUREMENT warm_dataset_stat_seconds={warm_timings['dataset_stat_seconds']:.6f}",
        f"MEASUREMENT warm_dataset_hash_seconds={warm_timings['dataset_hash_seconds']:.6f}",
        f"MEASUREMENT warm_dataset_bytes_read={warm_timings['dataset_bytes_read']}",
        f"MEASUREMENT warm_tool_key_seconds={warm_timings['tool_key_seconds']:.6f}",
        f"MEASUREMENT warm_winner_import_seconds={warm_curator.import_seconds:.6f}",
        f"MEASUREMENT uncached_curate_seconds={uncached_seconds:.6f}",
        f"MEASUREMENT uncached_validate_seconds={uncached.validate_seconds:.6f}",
        f"MEASUREMENT uncached_validate_calls={uncached.validate_calls}",
        f"MEASUREMENT warm_curate_seconds={warm_curate_seconds:.6f}",
        f"MEASUREMENT warm_curate_tool_key_seconds={warmed.cache.timings['tool_key_seconds']:.6f}",
        f"MEASUREMENT warm_curate_import_seconds={warmed.import_seconds:.6f}",
        f"MEASUREMENT warm_curate_import_calls={warmed.import_calls}",
    ]
    print("\n".join(lines))
