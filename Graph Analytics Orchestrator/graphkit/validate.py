"""Check tool folders against the tool contract.

    python -m graphkit.validate path/to/tool_folder [more folders...]

Exit code 0 means every folder passed (warnings allowed); 1 means at least one error.
The registry's automated checks run exactly this command on every pull request.
"""
from __future__ import annotations

import ast
import contextlib
import inspect
import io
import json
import re
import sys
import time
from pathlib import Path

from .contract import MAX_OUTPUT_BYTES, OUTPUT_KEYS, TIME_LIMIT_SECONDS
from .loader import load_tool
from .menu import CATEGORIES, INFRA_TOOLS, MENU
from .store import GraphStore

BOOTCAMP_TOOLS = {"node_degree": "structure"}
BANNED_LIBRARIES = {"networkx", "igraph", "graph_tool", "rustworkx", "networkit", "snap", "cugraph",
                    "scipy", "sklearn", "pandas", "torch", "tensorflow"}
BANNED_STDLIB = {"socket", "urllib", "http", "ftplib", "smtplib", "subprocess", "multiprocessing", "shutil"}
ALLOWED_EXTRA = {"numpy", "graphkit"}
JSON_TYPES = {"string": str, "integer": int, "number": (int, float), "boolean": bool, "array": list, "object": dict}


class Report:
    def __init__(self, folder: Path):
        self.folder = folder
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def print(self) -> None:
        status = "PASS" if not self.errors else "FAIL"
        print(f"[{status}] {self.folder}")
        for e in self.errors:
            print(f"   error:   {e}")
        for w in self.warnings:
            print(f"   warning: {w}")


# ---------------------------------------------------------------- manifest
def _type_ok(value, schema_type: str) -> bool:
    expected = JSON_TYPES.get(schema_type)
    if expected is None:
        return False
    if schema_type in ("integer", "number") and isinstance(value, bool):
        return False
    return isinstance(value, expected)


def check_manifest(m: dict, r: Report) -> str:
    """Returns the tool kind: 'menu', 'infra' or 'bootcamp'."""
    for key in ("name", "implementation_id", "author", "tier", "category", "description", "parameters", "examples"):
        if key not in m:
            r.error(f"tool.json is missing '{key}'")
    name, tier, category = m.get("name", ""), m.get("tier", ""), m.get("category", "")
    kind = "menu"
    if name in MENU:
        exp_tier, exp_cat, _ = MENU[name]
        if tier != exp_tier:
            r.error(f"tier is '{tier}' but '{name}' is a {exp_tier} tool")
        if category != exp_cat:
            r.error(f"category is '{category}' but '{name}' is in category '{exp_cat}'")
    elif name in INFRA_TOOLS:
        kind = "infra"
    elif name in BOOTCAMP_TOOLS:
        kind = "bootcamp"
    else:
        r.error(f"'{name}' is not a tool name from the menu (check the spelling)")
    if category not in CATEGORIES:
        r.error(f"category must be one of {', '.join(CATEGORIES)}")
    if "TODO" in json.dumps(m) or "YOUR_ID" in json.dumps(m):
        r.error("tool.json still contains TODO or YOUR_ID placeholders")
    author = m.get("author", "")
    if not isinstance(author, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", author or ""):
        r.error("author must be your student id (letters, digits, - or _)")
    elif kind == "menu" and m.get("implementation_id") != f"{name}.{author}":
        r.error(f"implementation_id must be '{name}.{author}'")
    desc = m.get("description", "")
    if not isinstance(desc, str) or len(desc) < 60:
        r.error("description is too short: say what the tool computes, which questions it answers, "
                "which graphs it works on and what it returns")
    elif len(desc) > 1024:
        r.error("description is longer than 1024 characters")

    params = m.get("parameters", {})
    if not isinstance(params, dict) or params.get("type") != "object" or not isinstance(params.get("properties"), dict):
        r.error('parameters must be {"type": "object", "properties": {...}, "required": [...]}')
        return kind
    props, required = params["properties"], params.get("required", [])
    for p in required:
        if p not in props:
            r.error(f"required parameter '{p}' is not in properties")
    for pname, spec in props.items():
        if not isinstance(spec, dict) or spec.get("type") not in JSON_TYPES:
            r.error(f"parameter '{pname}' needs a type: one of {', '.join(JSON_TYPES)}")
        elif not spec.get("description"):
            r.error(f"parameter '{pname}' needs a description (the LLM reads it)")
    if name != "list_graphs":
        if props.get("graph_id", {}).get("type") != "string" or "graph_id" not in required:
            r.error("parameters must include a required string 'graph_id'")
    if "top_k" in props:
        spec = props["top_k"]
        if spec.get("type") != "integer" or spec.get("maximum", 101) > 100 or "default" not in spec:
            r.error("top_k must be an integer with a default and a maximum of at most 100")

    examples = m.get("examples")
    if not isinstance(examples, list) or not examples:
        r.error("examples must be a list with at least one example call, e.g. [{\"graph_id\": \"karate\"}]")
    else:
        for i, ex in enumerate(examples, 1):
            if not isinstance(ex, dict):
                r.error(f"example {i} must be an object of parameters")
                continue
            for p in required:
                if p not in ex:
                    r.error(f"example {i} is missing required parameter '{p}'")
            for p, v in ex.items():
                if p not in props:
                    r.error(f"example {i} uses '{p}', which is not in parameters")
                elif not _type_ok(v, props[p].get("type", "")):
                    r.error(f"example {i}: '{p}' should be of type {props[p].get('type')}")
    return kind


# ---------------------------------------------------------------- source code
def check_source(tool_py: Path, r: Report) -> None:
    try:
        tree = ast.parse(tool_py.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        r.error(f"tool.py has a syntax error: {exc}")
        return
    stdlib = set(sys.stdlib_module_names)
    for node in ast.walk(tree):
        mods = []
        if isinstance(node, ast.Import):
            mods = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                r.error("relative imports are not allowed: put all your code in tool.py")
                continue
            mods = [node.module or ""]
        for mod in mods:
            top = mod.split(".")[0]
            if top in BANNED_LIBRARIES:
                r.error(f"import of '{mod}' is not allowed: implement the algorithm yourself "
                        f"(standard library, NumPy and graphkit only)")
            elif top in BANNED_STDLIB:
                r.error(f"import of '{mod}' is not allowed: tools make no network calls and run no processes")
            elif top not in stdlib and top not in ALLOWED_EXTRA:
                r.error(f"import of '{mod}' is not allowed (standard library, NumPy and graphkit only)")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "open":
                r.error("tools must not open files: get graphs from the store")
            elif node.func.id in ("eval", "exec", "__import__"):
                r.error(f"'{node.func.id}' is not allowed in tools")
            elif node.func.id == "print":
                r.warn("tool.py calls print(); tools must print nothing (remove debugging prints)")


def check_signature(run, m: dict, r: Report) -> None:
    try:
        sig = inspect.signature(run)
    except (TypeError, ValueError):
        r.error("cannot read the signature of run()")
        return
    names = list(sig.parameters)
    if not names or names[0] != "store":
        r.error("run() must take 'store' as its first parameter: def run(store, graph_id, **params)")
    if m.get("name") != "list_graphs" and (len(names) < 2 or names[1] != "graph_id"):
        r.error("run() must take 'graph_id' as its second parameter: def run(store, graph_id, **params)")
    has_kwargs = any(p.kind is inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
    for pname in m.get("parameters", {}).get("properties", {}):
        if pname not in sig.parameters and not has_kwargs:
            r.error(f"run() does not accept parameter '{pname}' from tool.json")


# ---------------------------------------------------------------- behaviour
def _walk_dicts(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from _walk_dicts(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_dicts(v)


def check_output(out, store: GraphStore, where: str, r: Report) -> str | None:
    """Checks one output; returns its canonical JSON (or None if it is unusable)."""
    if not isinstance(out, dict):
        r.error(f"{where}: run() returned {type(out).__name__}, not a dict (use ok() or error())")
        return None
    if set(out) != set(OUTPUT_KEYS):
        r.error(f"{where}: output keys must be exactly {', '.join(OUTPUT_KEYS)}; got {', '.join(sorted(out))}")
        return None
    try:
        text = json.dumps(out, allow_nan=False, sort_keys=True)
    except (TypeError, ValueError) as exc:
        r.error(f"{where}: output is not valid JSON ({exc}); convert NumPy values with float()/int() "
                f"and avoid NaN or infinity")
        return None
    size = len(text.encode("utf-8"))
    if size > MAX_OUTPUT_BYTES:
        r.error(f"{where}: output is {size} bytes; the limit is {MAX_OUTPUT_BYTES} (use top_k, summarise)")
    if out["status"] not in ("ok", "error"):
        r.error(f"{where}: status must be 'ok' or 'error'")
    elif out["status"] == "ok":
        if out["error"] is not None:
            r.error(f"{where}: error must be null when status is 'ok'")
        if not isinstance(out["summary"], str) or not out["summary"].strip():
            r.error(f"{where}: summary must be a non-empty sentence")
    else:
        if not isinstance(out["error"], str) or not out["error"].strip():
            r.error(f"{where}: an error result needs an error message")
    for d in _walk_dicts(out["result"]):
        if "id" in d and not isinstance(d.get("label"), str):
            r.error(f"{where}: node {d['id']!r} has no 'label'; return nodes with node_ref(graph, node)")
            break
    rgid = out["result_graph_id"]
    if rgid is not None and (not isinstance(rgid, str) or not store.has_graph(rgid)):
        r.error(f"{where}: result_graph_id {rgid!r} is not a registered graph (use store.subgraph)")
    return text


def _call(run, store, params):
    buf = io.StringIO()
    start = time.perf_counter()
    with contextlib.redirect_stdout(buf):
        out = run(store, **params)
    return out, time.perf_counter() - start, buf.getvalue()


def check_behaviour(tool, kind: str, r: Report) -> None:
    examples = tool.manifest.get("examples") or []
    for i, ex in enumerate(examples, 1):
        where = f"example {i} {json.dumps(ex)}"
        store1, store2 = GraphStore(), GraphStore()
        try:
            out1, secs, printed = _call(tool.run, store1, ex)
        except Exception as exc:
            r.error(f"{where}: run() crashed with {type(exc).__name__}: {exc}")
            continue
        if printed:
            r.error(f"{where}: the tool printed to standard output; tools must print nothing")
        if secs > TIME_LIMIT_SECONDS:
            r.error(f"{where}: took {secs:.1f}s; the limit is {TIME_LIMIT_SECONDS}s")
        elif secs > TIME_LIMIT_SECONDS / 3:
            r.warn(f"{where}: took {secs:.1f}s; slower laptops may exceed the {TIME_LIMIT_SECONDS}s limit")
        text1 = check_output(out1, store1, where, r)
        if text1 is None:
            continue
        if out1["status"] != "ok":
            r.error(f"{where}: examples should succeed, but it returned an error: {out1['error']}")
        try:
            out2, _, _ = _call(tool.run, store2, ex)
            if json.dumps(out2, allow_nan=False, sort_keys=True) != text1:
                r.error(f"{where}: two runs gave different outputs; tools must be deterministic "
                        f"(use a seed parameter, and sort when order is otherwise arbitrary)")
        except Exception:
            r.error(f"{where}: the second run crashed; tools must not depend on state from earlier calls")

    if kind != "infra" or tool.name != "list_graphs":
        base = dict(examples[0]) if examples else {}
        base["graph_id"] = "no_such_graph"
        store = GraphStore()
        try:
            out = tool.run(store, **base)
        except Exception as exc:
            r.error(f"an unknown graph_id made run() crash ({type(exc).__name__}); return error(...) instead")
            return
        check_output(out, store, "unknown graph_id", r)
        if isinstance(out, dict) and out.get("status") != "error":
            r.error("an unknown graph_id must give status 'error'")


# ---------------------------------------------------------------- driver
def validate(folder: str | Path) -> Report:
    folder = Path(folder)
    r = Report(folder)
    if not (folder / "tool.json").is_file() or not (folder / "tool.py").is_file():
        r.error("a tool folder must contain tool.json and tool.py")
        return r
    try:
        manifest = json.loads((folder / "tool.json").read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        r.error(f"tool.json is not valid JSON: {exc}")
        return r
    kind = check_manifest(manifest, r)
    check_source(folder / "tool.py", r)
    if kind == "menu":
        if not (folder / "README.md").is_file():
            r.error("README.md is missing")
        n_tests = sum(len(re.findall(r"^def test_", p.read_text(encoding="utf-8"), re.M))
                      for p in (folder / "tests").glob("test_*.py")) if (folder / "tests").is_dir() else 0
        if n_tests < 5:
            r.warn(f"found {n_tests} test functions in tests/; write at least five")
    if r.errors:  # do not import code whose static checks failed
        return r
    try:
        tool = load_tool(folder)
    except Exception as exc:
        r.error(f"tool.py could not be loaded: {type(exc).__name__}: {exc}")
        return r
    check_signature(tool.run, manifest, r)
    if not r.errors:
        check_behaviour(tool, kind, r)
    return r


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    reports = [validate(f) for f in argv]
    for rep in reports:
        rep.print()
    failed = sum(1 for rep in reports if rep.errors)
    print(f"\n{len(reports) - failed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
