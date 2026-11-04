"""Call any tool from the command line and print its output.

    python run_tool.py infra_tools/lookup_node graph_id=airports name=Chennai
    python run_tool.py bootcamp/node_degree graph_id=karate node=m1
    python run_tool.py registry/tools/pagerank/s123 graph_id=airports top_k=5

Values are read as JSON when possible (top_k=5 is a number, flag=true a boolean), else as text.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from graphkit import GraphStore, load_tool  # noqa: E402


def parse(arg: str):
    key, sep, value = arg.partition("=")
    if not sep:
        sys.exit(f"Arguments look like name=value; got {arg!r}")
    try:
        return key, json.loads(value)
    except json.JSONDecodeError:
        return key, value


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    tool = load_tool(sys.argv[1])
    params = dict(parse(a) for a in sys.argv[2:])
    print(json.dumps(tool.run(GraphStore(), **params), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
