
"""Dynamic tool discovery and planning context for the graph orchestrator."""

from pathlib import Path

from graphkit import discover
from graphkit.llm import tool_schema
FINAL_ANSWER_INSTRUCTIONS = """
FINAL ANSWER FORMAT:

When you have completed the analysis, return your final response
as valid JSON only, without Markdown code fences.

Use this exact structure:

{
    "status": "answered",
    "answer_text": "A concise explanation of the result.",
    "answer": {
        "type": "number",
        "value": 34
    }
}

Valid answer types:
- number
- boolean
- node
- node_list
- path
- text

Valid statuses:
- answered
- clarification_needed
- unsupported
- error

For clarification_needed, unsupported, and error,
provide a meaningful answer_text.

Never invent graph facts.
Every graph-related fact must be supported by tool outputs.
""".strip()

class Planner:
    """Discovers graph tools and prepares the agent's tool-calling context."""

    def __init__(self, project_root=None):
        self.project_root = (
            Path(project_root).resolve()
            if project_root
            else Path(__file__).resolve().parent.parent
        )

        self.tools = {}
        self.schemas = []

        self._discover_tools()

    def _discover_tools(self):
        """Discover all tools from infrastructure and algorithm registries."""

        infra_dir = self.project_root / "infra_tools"
        registry_dir = self.project_root / "registry" / "tools"

        discovered = discover(infra_dir, registry_dir)

        for tool in discovered:
            if tool.name in self.tools:
                raise ValueError(
                    f"Duplicate tool name discovered: {tool.name}"
                )

            self.tools[tool.name] = tool

        if not self.tools:
            raise RuntimeError("No graph tools were discovered.")

        # Convert every discovered manifest into an OpenAI-compatible schema.
        self.schemas = [
            tool_schema(tool.manifest)
            for tool in self.tools.values()
        ]

    def get_tools(self):
        """Return the discovered tools indexed by their names."""
        return self.tools

    def get_schemas(self):
        """Return tool schemas for Gemini function calling."""
        return self.schemas

    def get_system_prompt(self, store):
        """Build the system prompt using the current graph inventory."""

        graphs = store.list_graphs()

        graph_description = "\n".join(
            (
                f"- ID: {graph['graph_id']}; "
                f"Description: {graph['description']}; "
                f"Nodes: {graph['nodes']}; "
                f"Edges: {graph['edges']}; "
                f"Directed: {graph['directed']}; "
                f"Weighted: {graph['weighted']}"
            )
            for graph in graphs
        )

        tool_description = "\n".join(
            (
                f"- {tool.name}: {tool.manifest['description']}"
            )
            for tool in self.tools.values()
        )

        return f"""
You are an intelligent graph analytics assistant.

Your task is to answer users' natural-language questions by selecting
and executing the available graph tools.

AVAILABLE GRAPHS:
{graph_description}

AVAILABLE TOOLS:
{tool_description}

IMPORTANT RULES:

1. Use graph tools to obtain graph facts. Never invent graph statistics,
   node properties, paths, rankings, or other results.

2. Select tools based on the user's actual question.

3. If the user mentions a node by its label rather than its ID,
   use lookup_node to identify the correct node first.

4. If a question requires multiple operations, execute them in sequence.

5. When a tool returns result_graph_id, use that ID as the graph_id
   for subsequent operations when they concern the derived graph.

6. Use only graph IDs present in the available graph inventory or
   returned by earlier tool calls.

7. Keep tool calls minimal. Do not perform unnecessary operations.

8. If the question is ambiguous, ask for clarification rather than
   guessing.

9. If the requested operation is unsupported by the available tools,
   clearly explain that it is unsupported.

10. Base every factual claim in your final answer on tool results.

11. Do not claim that a tool succeeded unless its output indicates
    success.

12. Return a clear, concise answer to the user's question.
""".strip() + "\\n\\n" + FINAL_ANSWER_INSTRUCTIONS