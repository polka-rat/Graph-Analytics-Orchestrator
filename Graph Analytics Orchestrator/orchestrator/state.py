
from typing import Annotated, Any
from typing_extensions import TypedDict
import operator


class AgentState(TypedDict, total=False):
    """
    Shared state passed between nodes in the LangGraph workflow.
    """

    # Conversation history.
    # operator.add appends new messages instead of replacing old ones.
    messages: Annotated[list[dict[str, Any]], operator.add]

    # Original user question.
    question: str

    # Number of tool calls made so far.
    tool_calls_count: int

    # Maximum allowed tool calls for one query.
    max_tool_calls: int

    # Names of tools executed during this query.
    tools_used: list[str]

    # Final response.
    answer_text: str
    answer: dict[str, Any] | None

    # Final status: answered, clarification_needed, unsupported, or error.
    status: str

    # Error details, if any.
    error: str | None
