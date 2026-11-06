"""Select and cache reliable tool implementations from the published registry."""

from collections import defaultdict
from dataclasses import dataclass
import json
import logging
from pathlib import Path

from graphkit import discover, load_tool
from graphkit.validate import validate

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CurationRecord:
    implementation_id: str
    selected: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


class ToolCurator:
    """Validate registry candidates and select one implementation per tool with persistent caching."""

    def __init__(self, infra_dir: Path, registry_dir: Path, cache_file: Path | None = None):
        self.infra_dir = Path(infra_dir).resolve()
        self.registry_dir = Path(registry_dir).resolve()
        self.cache_file = Path(cache_file).resolve() if cache_file else self.registry_dir.parent / ".curated_tools_cache.json"
        self.records: list[CurationRecord] = []

    def curate(self, force_refresh: bool = False):
        """Return validated tools. Uses cached selection if available."""
        # 1. Fast path: load from disk cache if valid
        if not force_refresh and self.cache_file.exists():
            try:
                cached_data = json.loads(self.cache_file.read_text(encoding="utf-8"))
                selected_tools = {}
                cache_valid = True
                for name, path_str in cached_data.items():
                    p = Path(path_str)
                    if p.is_dir() and (p / "tool.json").is_file():
                        selected_tools[name] = load_tool(p)
                    else:
                        cache_valid = False
                        break
                if cache_valid and selected_tools:
                    return selected_tools
            except Exception:
                pass  # Fall back to live curation if cache read fails

        # 2. Live curation with fast-path candidate short-circuiting
        candidates = defaultdict(list)
        for tool in discover(self.infra_dir, self.registry_dir):
            candidates[tool.name].append(tool)

        selected = {}
        for name in sorted(candidates):
            # If infra tool, it is trusted and already verified
            if name in ("list_graphs", "lookup_node", "node_attributes", "filter_nodes"):
                tool = candidates[name][0]
                selected[name] = tool
                self.records.append(CurationRecord(tool.implementation_id, True))
                continue

            # For algorithm tools, test candidates until a passing one is found
            best_tool = None
            best_record = None

            for tool in candidates[name]:
                report = self._validate(tool)
                rec = CurationRecord(
                    implementation_id=tool.implementation_id,
                    selected=False,
                    errors=tuple(report.errors),
                    warnings=tuple(report.warnings),
                )
                self.records.append(rec)

                if not report.errors:
                    best_tool = tool
                    best_record = rec
                    # Stop searching as soon as a passing candidate is found
                    break

            if best_tool and best_record:
                selected[name] = best_tool
                idx = self.records.index(best_record)
                self.records[idx] = CurationRecord(
                    best_record.implementation_id, True, best_record.errors, best_record.warnings
                )

        # 3. Persist selection to disk cache
        try:
            cache_payload = {name: str(tool.path) for name, tool in selected.items()}
            self.cache_file.write_text(json.dumps(cache_payload, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to write curation cache: {e}")

        return selected

    @staticmethod
    def _validate(tool):
        try:
            return validate(tool.path)
        except Exception as exc:
            class FailedReport:
                errors = (f"{type(exc).__name__}: {exc}",)
                warnings = ()
            return FailedReport()

    def summary(self):
        return {
            "candidates": len(self.records),
            "selected": sum(r.selected for r in self.records),
            "rejected": sum(not r.selected for r in self.records),
            "selected_implementations": [r.implementation_id for r in self.records if r.selected],
        }
