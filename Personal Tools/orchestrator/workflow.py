
"""LangGraph workflow for the graph analytics orchestrator."""

import json

from langgraph.graph import StateGraph, START, END

from orchestrator.state import AgentState
from orchestrator.agent import create_agent_node
from orchestrator.executor import create_executor_node


def route_after_agent(state):
    """Decide whether to execute tools, finish, or stop at the limit."""

    messages = state.get("messages", [])

    if not messages:
        return "end"

    last_message = messages[-1]
    tool_calls = last_message.get("tool_calls", [])

    # No tool calls: Gemini has produced its final answer.
    if not tool_calls:
        return "end"

    # Do not execute any more tools after reaching the limit.
    if state.get("tool_calls_count", 0) >= state.get("max_tool_calls", 5):
        return "limit"

    return "executor"


def create_limit_node():
    """Create a node that returns an error when the tool limit is exceeded."""

    def limit_node(state):
        max_calls = state.get("max_tool_calls", 5)

        message = (
            f"The request could not be completed within the "
            f"{max_calls}-tool-call limit."
        )

        payload = {
            "status": "error",
            "answer_text": message,
            "answer": {
                "type": "text",
                "value": message,
            },
        }

        return {
            "answer_text": json.dumps(payload),
            "status": "error",
            "error": message,
        }

    return limit_node


def build_workflow(client, planner, store, trace):
    """Build and compile the LangGraph workflow."""

    agent_node = create_agent_node(client, planner, trace)
    executor_node = create_executor_node(planner, store, trace)
    limit_node = create_limit_node()

    workflow = StateGraph(AgentState)

    workflow.add_node("agent", agent_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("limit", limit_node)

    workflow.add_edge(START, "agent")

    workflow.add_conditional_edges(
        "agent",
        route_after_agent,
        {
            "executor": "executor",
            "limit": "limit",
            "end": END,
        },
    )

    # Always return to the agent after tool execution.
    # This gives Gemini an opportunity to interpret the result.
    workflow.add_edge("executor", "agent")

    workflow.add_edge("limit", END)

    return workflow.compile()
