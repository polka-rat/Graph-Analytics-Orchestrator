"""Disk cache of tool-contract validation reports.

Invalidation trusts file content, not the clock. A warm start uses size and
modification time only to avoid re-reading bytes that already produced a
stored content digest.

Dataset fingerprint
    Computed once per :class:`ValidationCache` instance, never once per tool.
    The files are ``data/graphs.json`` and every ``nodes.csv`` and ``edges.csv``
    under ``data/``. ``data/README.md`` is not an input.
    Each file is recorded with its path, size, ``mtime_ns``, and sha256.
    The digest embedded in tool keys is sha256 over those path-ordered
    per-file digests. A warm start ``stat``s the files and, when every size
    and ``mtime_ns`` still matches, reuses the stored digest and does not open
    the CSVs. If a size or mtime differs, only the files whose stat changed
    are hashed again and the combined digest is rebuilt. A missing or corrupt
    fingerprint hashes every file.
    Same-size, same-mtime content replacement is the accepted limit of the
    fast path. It is cleared by a size or mtime change, by deleting the
    fingerprint file, or by bumping :data:`CACHE_VERSION`.

Tool-folder entry
    One JSON report per folder, under ``.cache/tool_validation/tools/``.
    The entry stores the dataset digest, a digest of ``validate.py``,
    ``menu.py`` and ``contract.py``, :data:`CACHE_VERSION`, the interpreter
    ``(major, minor)``, the content hash of the tool inputs, and the size
    and ``mtime_ns`` of those inputs (``tool.json``, ``tool.py``, ``README.md``
    when present, and ``tests/test_*.py``).
    When those stats and the shared digests still match, the stored errors
    and warnings are a hit and the tool files are not read.
    When the stats differ but the shared digests match, the tool bytes are
    hashed. If that content hash still matches, the stored stats are updated
    and the report is kept (a checkout or ``touch`` that did not change
    bytes). If the hash differs, the entry is discarded and the caller runs
    ``validate``.
    A changed dataset digest, validator digest, Python minor version, or
    :data:`CACHE_VERSION` misses every folder. A changed tool misses only
    that folder. Corrupt JSON, a truncated file, or a missing field is a
    miss: the bad file is deleted and validation runs. There is no TTL.

The standalone ``python -m graphkit.validate`` command does not use this
module. Cache files are local and must not be committed.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

CACHE_VERSION = 1

_GRAPHKIT_DIR = Path(__file__).resolve().parent
_CODE_FILES = ("validate.py", "menu.py", "contract.py")
_TOOL_INPUT_NAMES = ("tool.json", "tool.py", "README.md")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _combine_digests(items: list[tuple[str, str]]) -> str:
    """sha256 over path-ordered ``(relative path, per-file sha256)`` pairs."""
    digest = hashlib.sha256()
    for rel, file_hash in items:
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(file_hash))
        digest.update(b"\0")
    return digest.hexdigest()


def _atomic_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _read_json(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError, TypeError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def _stat_record(path: Path, root: Path) -> dict:
    stat = path.stat()
    return {
        "path": path.relative_to(root).as_posix(),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }


def _stats_match(stored: list, current: list[dict]) -> bool:
    if not isinstance(stored, list) or len(stored) != len(current):
        return False
    for old, new in zip(stored, current):
        if not isinstance(old, dict):
            return False
        if old.get("path") != new["path"] or old.get("size") != new["size"] or old.get("mtime_ns") != new["mtime_ns"]:
            return False
        if not isinstance(old.get("sha256"), str):
            return False
    return True


class ValidationCache:
    """Content-addressed validation reports with a stat fast path."""

    def __init__(self, project_root, cache_dir=None, data_dir=None, cache_version=None):
        self.project_root = Path(project_root).resolve()
        self.cache_dir = Path(cache_dir) if cache_dir else self.project_root / ".cache" / "tool_validation"
        self.data_dir = Path(data_dir) if data_dir else self.project_root / "data"
        self.cache_version = CACHE_VERSION if cache_version is None else cache_version
        self.timings = {
            "dataset_stat_seconds": 0.0,
            "dataset_hash_seconds": 0.0,
            "dataset_bytes_read": 0,
            "code_fingerprint_seconds": 0.0,
            "code_bytes_read": 0,
            "tool_key_seconds": 0.0,
            "tool_bytes_read": 0,
        }
        self.dataset_mode = ""
        self.dataset_hashed_paths: list[str] = []
        self._dataset_digest: str | None = None
        self._code_digest: str | None = None

    def entry_path(self, folder: Path) -> Path:
        key = hashlib.sha256(str(Path(folder).resolve()).encode("utf-8")).hexdigest()
        return self.cache_dir / "tools" / f"{key}.json"

    def fingerprint_dataset(self) -> str:
        """Return the dataset content digest, stating files when the record matches."""
        if self._dataset_digest is None:
            self._dataset_digest = self._fingerprint(
                files=self._dataset_files(),
                root=self.data_dir if self.data_dir.exists() else self.project_root,
                record_path=self.cache_dir / "dataset_fingerprint.json",
                stat_key="dataset_stat_seconds",
                hash_key="dataset_hash_seconds",
                bytes_key="dataset_bytes_read",
                hashed_paths=self.dataset_hashed_paths,
                mode_attr="dataset_mode",
            )
        return self._dataset_digest

    def fingerprint_code(self) -> str:
        """Return the digest of the validator modules, using the same stat rule."""
        if self._code_digest is None:
            files = [_GRAPHKIT_DIR / name for name in _CODE_FILES]
            self._code_digest = self._fingerprint(
                files=files,
                root=_GRAPHKIT_DIR,
                record_path=self.cache_dir / "code_fingerprint.json",
                stat_key="code_fingerprint_seconds",
                hash_key="code_fingerprint_seconds",
                bytes_key="code_bytes_read",
                hashed_paths=None,
                mode_attr="",
            )
        return self._code_digest

    def lookup(self, folder: Path) -> dict | None:
        """Return the stored report for ``folder``, or None when it must be validated.

        A hit includes ``name``, ``implementation_id``, ``errors``, and ``warnings``.
        Tool bytes are read only when size or mtime changed and the shared
        digests still match.
        """
        import time

        dataset_digest = self.fingerprint_dataset()
        code_digest = self.fingerprint_code()
        started = time.perf_counter()
        try:
            return self._lookup_tool(Path(folder), dataset_digest, code_digest)
        finally:
            self.timings["tool_key_seconds"] += time.perf_counter() - started

    def store(self, folder: Path, report, name: str, implementation_id: str) -> dict:
        """Persist the report ``validate`` just returned for ``folder``."""
        import time

        started = time.perf_counter()
        try:
            dataset_digest = self.fingerprint_dataset()
            code_digest = self.fingerprint_code()
            folder = Path(folder)
            files = _tool_input_files(folder)
            stats = [_stat_record(path, folder) for path in files]
            hashed = self._hash_files(files, "tool_bytes_read")
            for record, file_hash in zip(stats, hashed):
                record["sha256"] = file_hash
            payload = self._payload(
                folder,
                stats,
                _combine_digests([(item["path"], item["sha256"]) for item in stats]),
                dataset_digest,
                code_digest,
                name,
                implementation_id,
                list(report.errors),
                list(report.warnings),
            )
            _atomic_write(self.entry_path(folder), payload)
            return payload
        finally:
            self.timings["tool_key_seconds"] += time.perf_counter() - started

    def _dataset_files(self) -> list[Path]:
        if not self.data_dir.is_dir():
            return []
        found: dict[str, Path] = {}
        graphs = self.data_dir / "graphs.json"
        if graphs.is_file():
            found[graphs.resolve().as_posix()] = graphs
        for pattern in ("nodes.csv", "edges.csv"):
            for path in self.data_dir.rglob(pattern):
                if path.is_file():
                    found[path.resolve().as_posix()] = path
        return sorted(found.values(), key=lambda path: path.relative_to(self.data_dir).as_posix())

    def _fingerprint(
        self,
        files: list[Path],
        root: Path,
        record_path: Path,
        stat_key: str,
        hash_key: str,
        bytes_key: str,
        hashed_paths: list[str] | None,
        mode_attr: str,
    ) -> str:
        import time

        started = time.perf_counter()
        current = [_stat_record(path, root) for path in files]
        self.timings[stat_key] += time.perf_counter() - started
        stored = _read_json(record_path)
        stored_files = stored.get("files") if stored else None
        if (
            stored
            and stored.get("cache_version") == self.cache_version
            and _stats_match(stored_files, current)
            and isinstance(stored.get("digest"), str)
        ):
            if mode_attr:
                setattr(self, mode_attr, "stat")
            return stored["digest"]

        reusable = {}
        if stored and stored.get("cache_version") == self.cache_version and isinstance(stored_files, list):
            for item in stored_files:
                if isinstance(item, dict) and isinstance(item.get("sha256"), str):
                    reusable[item.get("path")] = item

        hash_started = time.perf_counter()
        hashed_items = []
        for path, stat in zip(files, current):
            previous = reusable.get(stat["path"])
            if (
                previous
                and previous.get("size") == stat["size"]
                and previous.get("mtime_ns") == stat["mtime_ns"]
            ):
                stat["sha256"] = previous["sha256"]
            else:
                stat["sha256"] = self._hash_files([path], bytes_key)[0]
                if hashed_paths is not None:
                    hashed_paths.append(stat["path"])
            hashed_items.append((stat["path"], stat["sha256"]))
        digest = _combine_digests(hashed_items)
        self.timings[hash_key] += time.perf_counter() - hash_started
        if mode_attr:
            setattr(self, mode_attr, "hash")
        _atomic_write(
            record_path,
            {
                "cache_version": self.cache_version,
                "digest": digest,
                "files": current,
            },
        )
        return digest

    def _hash_files(self, files: list[Path], bytes_key: str) -> list[str]:
        hashes = []
        for path in files:
            data = self._read_bytes(path, bytes_key)
            hashes.append(_sha256_bytes(data))
        return hashes

    def _read_bytes(self, path: Path, bytes_key: str) -> bytes:
        data = path.read_bytes()
        self.timings[bytes_key] += len(data)
        return data

    def _context_matches(self, entry: dict, dataset_digest: str, code_digest: str) -> bool:
        python = [sys.version_info[0], sys.version_info[1]]
        return (
            entry.get("cache_version") == self.cache_version
            and entry.get("python") == python
            and entry.get("dataset_digest") == dataset_digest
            and entry.get("validator_digest") == code_digest
        )

    def _lookup_tool(self, folder: Path, dataset_digest: str, code_digest: str) -> dict | None:
        path = self.entry_path(folder)
        entry = _read_json(path)
        if entry is None:
            if path.is_file():
                path.unlink()
            return None
        if not _report_shape(entry):
            path.unlink(missing_ok=True)
            return None
        files = _tool_input_files(folder)
        current = [_stat_record(file_path, folder) for file_path in files]
        if not self._context_matches(entry, dataset_digest, code_digest):
            return None
        if _stats_match(entry.get("stats"), current):
            return entry
        hashed = self._hash_files(files, "tool_bytes_read")
        content_hash = _combine_digests([(stat["path"], file_hash) for stat, file_hash in zip(current, hashed)])
        if content_hash != entry.get("content_hash"):
            return None
        for stat, file_hash in zip(current, hashed):
            stat["sha256"] = file_hash
        updated = dict(entry)
        updated["stats"] = current
        _atomic_write(path, updated)
        return updated

    def _payload(
        self,
        folder: Path,
        stats: list[dict],
        content_hash: str,
        dataset_digest: str,
        code_digest: str,
        name: str,
        implementation_id: str,
        errors: list,
        warnings: list,
    ) -> dict:
        return {
            "cache_version": self.cache_version,
            "python": [sys.version_info[0], sys.version_info[1]],
            "dataset_digest": dataset_digest,
            "validator_digest": code_digest,
            "content_hash": content_hash,
            "stats": stats,
            "name": name,
            "implementation_id": implementation_id,
            "errors": errors,
            "warnings": warnings,
            "folder": str(folder.resolve()),
        }


def _tool_input_files(folder: Path) -> list[Path]:
    files = []
    for name in _TOOL_INPUT_NAMES:
        path = folder / name
        if path.is_file():
            files.append(path)
    tests = folder / "tests"
    if tests.is_dir():
        files.extend(sorted(path for path in tests.glob("test_*.py") if path.is_file()))
    return files


def _report_shape(entry: dict) -> bool:
    if not isinstance(entry.get("name"), str) or not isinstance(entry.get("implementation_id"), str):
        return False
    if not isinstance(entry.get("content_hash"), str):
        return False
    if not isinstance(entry.get("errors"), list) or not isinstance(entry.get("warnings"), list):
        return False
    if not all(isinstance(item, str) for item in entry["errors"] + entry["warnings"]):
        return False
    return True
