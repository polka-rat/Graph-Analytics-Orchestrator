"""Check that your setup works. Run from the repository root:

    python smoke_test.py            # everything, including one call to your LLM provider
    python smoke_test.py --no-llm   # skip the LLM check
"""
import argparse
import importlib
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

results = []


def check(name, fn):
    try:
        detail = fn()
        results.append(True)
        print(f"  PASS  {name}" + (f": {detail}" if detail else ""))
    except Exception as exc:
        results.append(False)
        print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")


def python_version():
    if sys.version_info < (3, 10):
        raise RuntimeError(f"Python 3.10 or later is needed; this is {sys.version.split()[0]}")
    return sys.version.split()[0]


def packages():
    versions = []
    for name in ("numpy", "openai", "dotenv", "networkx", "pytest"):
        mod = importlib.import_module(name)
        versions.append(f"{name} {getattr(mod, '__version__', '')}".strip())
    return ", ".join(versions)


def datasets():
    from graphkit import GraphStore

    store = GraphStore()
    return ", ".join(f"{g['graph_id']} ({g['nodes']} nodes, {g['edges']} edges)" for g in store.list_graphs())


def infra_tools():
    from graphkit import discover
    from graphkit.validate import validate

    tools = discover(ROOT / "infra_tools")
    failed = [t.name for t in tools if validate(t.path).errors]
    if failed:
        raise RuntimeError(f"validator failed for {failed}")
    return f"{len(tools)} tools pass the validator"


def llm():
    from graphkit.llm import make_client, model_name

    client = make_client()
    tool = {"type": "function", "function": {
        "name": "ping", "description": "Replies pong. Call it when asked to ping.",
        "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "Any text."}},
                       "required": ["text"]}}}
    start = time.time()
    response = client.chat.completions.create(
        model=model_name(), tools=[tool],
        messages=[{"role": "user", "content": "Call the ping tool with text 'hello'."}])
    calls = response.choices[0].message.tool_calls or []
    if not calls or calls[0].function.name != "ping":
        raise RuntimeError("the model answered but did not call the tool; try another model")
    return f"{model_name()} called a tool in {time.time() - start:.1f}s"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-llm", action="store_true", help="skip the LLM provider check")
    args = parser.parse_args()
    print("Smoke test")
    check("Python version", python_version)
    check("Packages", packages)
    check("Datasets", datasets)
    check("Infrastructure tools", infra_tools)
    if args.no_llm:
        print("  SKIP  LLM function calling (--no-llm)")
    else:
        check("LLM function calling", llm)
    print("\nAll checks passed." if all(results) else "\nSome checks failed: fix them before you start.")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
