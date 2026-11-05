"""Select reliable tool implementations from the published registry."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from graphkit import discover
from graphkit.loader import find_tool_dirs, load_manifest, load_tool
from graphkit.validate import validate
from graphkit.validation_cache import ValidationCache


@dataclass(frozen=True)
class CurationRecord:
    """Validation outcome for one tool implementation."""

    implementation_id: str
    selected: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


class _Candidate:
    """One implementation, with a loader used only if it is selected."""

    def __init__(self, implementation_id, errors, warnings, loader):
        self.implementation_id = implementation_id
        self.errors = tuple(errors)
        self.warnings = tuple(warnings)
        self.loader = loader


class ToolCurator:
    """Validate registry candidates and select one implementation per tool."""

    def __init__(self, infra_dir, registry_dir, project_root=None, cache_dir=None, cache_version=None):
        self.infra_dir = infra_dir
        self.registry_dir = registry_dir
        self.project_root = (
            project_root if project_root is not None else Path(infra_dir).resolve().parent
        )
        self.cache_dir = cache_dir
        self.cache_version = cache_version
        self.records: list[CurationRecord] = []
        self.cache: ValidationCache | None = None
        self.validate_seconds = 0.0
        self.import_seconds = 0.0
        self.validate_calls = 0
        self.import_calls = 0

    def curate(self, use_cache=True):
        """Return validated tools grouped by their manifest tool name.

        ``use_cache=False`` is the original discover-then-validate loop and
        does not read or write the validation cache. The default caches each
        ``validate`` report and, on a later run, imports only the selected
        implementation of each tool.
        """
        self.records = []
        self.validate_seconds = 0.0
        self.import_seconds = 0.0
        self.validate_calls = 0
        self.import_calls = 0
        self.cache = None
        if not use_cache:
            return self._curate_uncached()
        return self._curate_cached()

    def _curate_uncached(self):
        """Today's startup path: import every candidate, then validate it."""
        started = time.perf_counter()
        discovered = discover(self.infra_dir, self.registry_dir)
        self.import_seconds += time.perf_counter() - started
        self.import_calls += len(discovered)

        candidates = defaultdict(list)
        for tool in discovered:
            candidates[tool.name].append(tool)

        grouped = {}
        for name in sorted(candidates):
            grouped[name] = [
                _Candidate(
                    tool.implementation_id,
                    (),
                    (),
                    _already_loaded(tool),
                )
                for tool in candidates[name]
            ]
            for candidate, tool in zip(grouped[name], candidates[name]):
                report = self._timed_validate(tool.path)
                candidate.errors = tuple(report.errors)
                candidate.warnings = tuple(report.warnings)
        return self._select(grouped)

    def _curate_cached(self):
        """Validate on a miss. On a hit, import only the selected tools."""
        root = self.project_root if self.project_root is not None else self.infra_dir
        self.cache = ValidationCache(
            root,
            cache_dir=self.cache_dir,
            cache_version=self.cache_version,
        )
        grouped = defaultdict(list)
        order = []
        for folder in find_tool_dirs(self.infra_dir, self.registry_dir):
            cached = self.cache.lookup(folder)
            if cached is None:
                manifest = load_manifest(folder)
                name = manifest["name"]
                implementation_id = manifest.get("implementation_id", name)
                report = self._timed_validate(folder)
                self.cache.store(folder, report, name, implementation_id)
                errors = report.errors
                warnings = report.warnings
            else:
                name = cached["name"]
                implementation_id = cached["implementation_id"]
                errors = cached["errors"]
                warnings = cached["warnings"]
            if name not in grouped:
                order.append(name)
            grouped[name].append(
                _Candidate(implementation_id, errors, warnings, _timed_loader(self, folder))
            )
        return self._select({name: grouped[name] for name in sorted(order)})

    def _timed_validate(self, folder):
        started = time.perf_counter()
        try:
            return self._validate_path(folder)
        finally:
            self.validate_seconds += time.perf_counter() - started
            self.validate_calls += 1

    def _select(self, grouped):
        selected = {}
        for name, candidates in grouped.items():
            validated = []
            for candidate in candidates:
                record = CurationRecord(
                    implementation_id=candidate.implementation_id,
                    selected=False,
                    errors=candidate.errors,
                    warnings=candidate.warnings,
                )
                self.records.append(record)
                if not candidate.errors:
                    validated.append((len(candidate.warnings), candidate, record))

            if validated:
                _, candidate, record = min(
                    validated,
                    key=lambda item: (item[0], item[1].implementation_id),
                )
                selected[name] = candidate.loader()
                self.records[self.records.index(record)] = CurationRecord(
                    implementation_id=record.implementation_id,
                    selected=True,
                    errors=record.errors,
                    warnings=record.warnings,
                )
        return selected

    @staticmethod
    def _validate_path(folder):
        """Validate one folder; a crash becomes a rejected report."""
        try:
            return validate(folder)
        except (OSError, TypeError, ValueError, KeyError, ImportError) as exc:
            class FailedReport:
                errors = (f"{type(exc).__name__}: {exc}",)
                warnings = ()

            return FailedReport()

    def summary(self):
        """Return compact curation counts for diagnostics and evaluation."""
        return {
            "candidates": len(self.records),
            "selected": sum(record.selected for record in self.records),
            "rejected": sum(not record.selected for record in self.records),
            "selected_implementations": [
                record.implementation_id
                for record in self.records
                if record.selected
            ],
            "rejection_reasons": {
                record.implementation_id: list(record.errors)
                for record in self.records
                if record.errors
            },
        }


def _already_loaded(tool):
    def load():
        return tool
    return load


def _timed_loader(curator, folder):
    def load():
        started = time.perf_counter()
        try:
            return load_tool(folder)
        finally:
            curator.import_seconds += time.perf_counter() - started
            curator.import_calls += 1
    return load
