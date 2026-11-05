
"""Executes tool calls requested by the LangGraph agent."""

import json

from graphkit.contract import error


def create_executor_node(planner, store, trace):
    """Create the LangGraph node responsible for executing tools."""

    def executor_node(state):
        messages = state.get("messages", [])

        if not messages:
            return {
                "status": "error",
                "error": "No messages available for tool execution.",
            }

        assistant_message = messages[-1]
        tool_calls = assistant_message.get("tool_calls", [])

        if not tool_calls:
            return {}

        tools = planner.get_tools()

        tool_messages = []
        tools_used = list(state.get("tools_used", []))

        current_count = state.get("tool_calls_count", 0)
        max_calls = state.get("max_tool_calls", 5)

        for tool_call in tool_calls:
            call_id = tool_call.get("id", "")
            function = tool_call.get("function", {})

            tool_name = function.get("name", "")
            raw_arguments = function.get("arguments", "{}")

            # Enforce the maximum tool-call limit.
            if current_count >= max_calls:
                output = error(
                    f"Maximum tool-call limit ({max_calls}) reached."
                )

            else:
                current_count += 1

                # Parse the tool arguments.
                try:
                    arguments = json.loads(raw_arguments)

                    if not isinstance(arguments, dict):
                        raise ValueError(
                            "Tool arguments must be a JSON object."
                        )

                except (json.JSONDecodeError, TypeError, ValueError) as exc:
                    arguments = {}
                    output = error(
                        f"Invalid arguments for {tool_name}: {exc}"
                    )

                else:
                    # Find and execute the requested tool.
                    tool = tools.get(tool_name)

                    if tool is None:
                        output = error(
                            f"Unknown tool: {tool_name}"
                        )
                    else:
                        output = tool.call(store, **arguments)

                # Record the tool execution.
                trace.tool_call(
                    tool_name,
                    arguments,
                    output,
                )

                if tool_name in tools:
                    tools_used.append(
                        tools[tool_name].implementation_id
                    )

            # Return the result to the LLM.
            tool_messages.append({
                "role": "tool",
                "tool_call_id": call_id,
                "content": json.dumps(output, default=str),
            })

        return {
            "messages": tool_messages,
            "tool_calls_count": current_count,
            "tools_used": tools_used,
        }

    return executor_node
