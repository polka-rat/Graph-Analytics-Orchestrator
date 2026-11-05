
"""Gemini-powered agent node for the LangGraph workflow."""

from graphkit.llm import model_name


def create_agent_node(client, planner, trace):
    """Create the Gemini agent node."""

    def agent_node(state):
        messages = state.get("messages", [])

        response = client.chat.completions.create(
            model=model_name(),
            messages=messages,
            tools=planner.get_schemas(),
            tool_choice="auto",
        )

        message = response.choices[0].message

        # Record every LLM response.
        trace.llm_call(model_name(), message)

        tool_calls = message.tool_calls or []

        # Preserve provider-specific fields such as thought_signature.
        if hasattr(message, "model_dump"):
            assistant_message = message.model_dump(exclude_none=True)
        else:
            assistant_message = {
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        },
                    }
                    for call in tool_calls
                ],
            }

        update = {
            "messages": [assistant_message]
        }

        # Gemini has finished calling tools and is providing its answer.
        if not tool_calls:
            answer_text = (
                message.content
                or "The model did not provide an answer."
            )

            update.update({
                "answer_text": answer_text,
                "status": "answered",
            })

        return update

    return agent_node
