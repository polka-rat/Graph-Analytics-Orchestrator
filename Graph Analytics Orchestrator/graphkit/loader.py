"""Load tools from their folders.

A tool folder holds tool.json (the manifest) and tool.py (with a run function).

    tool = load_tool("infra_tools/lookup_node")
    tool.name, tool.manifest["description"]
    tool.call(store, graph_id="airports", name="Chennai")

    tools = discover("infra_tools", "registry/tools")   # every tool folder below these
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .contract import error


@dataclass
class Tool:
    manifest: dict
    run: Callable[..., dict]
    path: Path

    @property
    def name(self) -> str:
        return self.manifest["name"]

    @property
    def implementation_id(self) -> str:
        return self.manifest.get("implementation_id", self.name)

    def call(self, store, **params) -> dict:
        """Call the tool, turning a crash into a contract error (used by agents)."""
        try:
            return self.run(store, **params)
        except Exception as exc:  # an agent must survive a broken tool
            return error(f"Tool '{self.name}' crashed: {type(exc).__name__}: {exc}")


def load_manifest(tool_dir: str | Path) -> dict:
    return json.loads((Path(tool_dir) / "tool.json").read_text(encoding="utf-8"))


def load_tool(tool_dir: str | Path) -> Tool:
    tool_dir = Path(tool_dir).resolve()
    manifest = load_manifest(tool_dir)
    module_name = "graphtool_" + hashlib.sha1(str(tool_dir).encode()).hexdigest()[:12]
    spec = importlib.util.spec_from_file_location(module_name, tool_dir / "tool.py")
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {tool_dir / 'tool.py'}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not callable(getattr(module, "run", None)):
        raise ImportError(f"{tool_dir / 'tool.py'} has no run() function")
    return Tool(manifest=manifest, run=module.run, path=tool_dir)


def discover(*roots: str | Path) -> list[Tool]:
    """Load every tool folder (any folder with a tool.json) under the given roots."""
    tools = []
    for root in roots:
        for manifest_path in sorted(Path(root).rglob("tool.json")):
            if "template" in manifest_path.parts:
                continue
            tools.append(load_tool(manifest_path.parent))
    return tools
