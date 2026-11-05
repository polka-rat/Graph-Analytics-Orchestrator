"""Run an offline integration demo without an LLM API key."""

from graphkit import GraphStore
from orchestrator.planner import Planner


def main():
    """Load the project, curate tools, and execute one representative call."""
    planner = Planner()
    store = GraphStore()
    lookup = planner.get_tools()["lookup_node"]
    result = lookup.call(store, graph_id="airports", name="Chennai")

    print("Graph Analytics Orchestrator demo")
    print(f"Loaded graphs: {len(store.list_graphs())}")
    print(f"Curated tools: {len(planner.get_tools())}")
    print(f"Curated candidates: {planner.curation['candidates']}")
    print(f"Lookup status: {result['status']}")
    if result["status"] == "ok":
        print(f"Lookup matches: {len(result['result'])}")


if __name__ == "__main__":
    main()
