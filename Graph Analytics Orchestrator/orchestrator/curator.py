"""Select reliable tool implementations from the published registry."""

from collections import defaultdict
from dataclasses import dataclass

from graphkit import discover
from graphkit.validate import validate


@dataclass(frozen=True)
class CurationRecord:
    """Validation outcome for one tool implementation."""

    implementation_id: str
    selected: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


class ToolCurator:
    """Validate registry candidates and select one implementation per tool."""

    def __init__(self, infra_dir, registry_dir):
        self.infra_dir = infra_dir
        self.registry_dir = registry_dir
        self.records: list[CurationRecord] = []

    def curate(self):
        """Return validated tools grouped by their manifest tool name."""
        candidates = defaultdict(list)
        for tool in discover(self.infra_dir, self.registry_dir):
            candidates[tool.name].append(tool)

        selected = {}
        for name in sorted(candidates):
            validated = []
            for tool in candidates[name]:
                report = self._validate(tool)
                record = CurationRecord(
                    implementation_id=tool.implementation_id,
                    selected=False,
                    errors=tuple(report.errors),
                    warnings=tuple(report.warnings),
                )
                self.records.append(record)
                if not report.errors:
                    validated.append((len(report.warnings), tool, record))

            if validated:
                _, tool, record = min(
                    validated,
                    key=lambda item: (item[0], item[1].implementation_id),
                )
                selected[name] = tool
                self.records[self.records.index(record)] = CurationRecord(
                    implementation_id=record.implementation_id,
                    selected=True,
                    errors=record.errors,
                    warnings=record.warnings,
                )

        return selected

    @staticmethod
    def _validate(tool):
        """Validate one candidate; malformed candidates are rejected."""
        try:
            return validate(tool.path)
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
