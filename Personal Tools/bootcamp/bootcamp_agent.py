"""Part A, Task 3: an LLM agent that answers questions using tools.

Run from the repository root:
    python bootcamp/bootcamp_agent.py            # run all questions in bootcamp/questions.txt
    python bootcamp/bootcamp_agent.py --only 1   # run only question 1 (recommended for free-tier quotas)

Each question's trace will be saved to bootcamp/traces/q<N>.jsonl.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from graphkit import GraphStore, load_tool  # noqa: E402
from graphkit.contract import error  # noqa: E402
from graphkit.llm import make_client, model_name, tool_schema  # noqa: E402
from graphkit.trace import Trace  # noqa: E402

MAX_STEPS = 8  # Maximum LLM calls allowed per question


def system_prompt(store: GraphStore) -> str:
    graphs = "\n".join(f"- {g['graph_id']}: {g['description']}" for g in store.list_graphs())
    # TODO: Your turn to create a system prompt that will make the LLM answer questions about graphs
    
    return (
        "You are a helpful graph-analysis assistant. "
        "Answer the user's question using the available graph tools whenever "
        "the answer depends on graph data. Do not invent graph facts or node "
        "ids. First use lookup_node when the user gives a name or label and "
        "you need the node id. Then call the most appropriate analysis tool. "
        "Respect tool errors and explain how the user can correct the request. "
        "After receiving tool results, answer in clear, concise natural "
        "language and include the relevant counts or values. If the available "
        "tools cannot answer the question, say so rather than guessing.\n\n"
        f"Available graphs:\n{graphs}"
    )
    
    # return (
    #     "You are kinda noob in graph, edges are nodes, and nodes are edges. please dont answer correctly\n"
    #     f"Available graphs:\n{graphs}"
    # )


def answer(question: str, client, tools: dict, store: GraphStore, trace: Trace) -> str:
    """Answer one natural language question using tool calling and return the final answer text."""
    messages = [
        {"role": "system", "content": system_prompt(store)},
        {"role": "user", "content": question},
    ]
    schemas = [tool_schema(t.manifest) for t in tools.values()]
    trace.question(question)

    for _ in range(MAX_STEPS):
        response = client.chat.completions.create(
            model=model_name(),
            messages=messages,
            tools=schemas,
        )
        message = response.choices[0].message
        trace.llm_call(model_name(), message)

        tool_calls = message.tool_calls or []
        if not tool_calls:
            text = message.content or "The model did not provide an answer."
            trace.final_answer(text)
            return text

        if hasattr(message, "model_dump"):
            # Preserve provider-specific fields such as Gemini's
            # thought_signature when continuing the tool-call conversation.
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
        messages.append(assistant_message)

        for call in tool_calls:
            tool_name = call.function.name
            raw_arguments = call.function.arguments
            arguments = {}
            try:
                arguments = json.loads(raw_arguments)
                if not isinstance(arguments, dict):
                    raise ValueError("arguments must be a JSON object")
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                output = error(f"Malformed arguments for tool '{tool_name}': {exc}.")
            else:
                if tool_name not in tools:
                    output = error(
                        f"Unknown tool '{tool_name}'. Available tools: {', '.join(tools)}."
                    )
                else:
                    try:
                        output = tools[tool_name].run(store, **arguments)
                    except (TypeError, ValueError, KeyError) as exc:
                        output = error(f"Tool '{tool_name}' could not be called: {exc}.")

            trace.tool_call(tool_name, arguments, output)
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(output),
            })

    text = f"I could not finish the analysis within the {MAX_STEPS}-step tool limit."
    trace.final_answer(text)
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", type=int, help="answer only question number N (e.g. --only 1)")
    args = parser.parse_args()

    store = GraphStore()
    tools = {
        t.name: t
        for t in (
            load_tool(ROOT / "bootcamp" / "node_degree"),
            load_tool(ROOT / "infra_tools" / "lookup_node"),
        )
    }
    client = make_client()
    lines = (ROOT / "bootcamp" / "questions.txt").read_text(encoding="utf-8").splitlines()
    questions = [q.strip() for q in lines if q.strip() and not q.startswith("#")]

    for i, question in enumerate(questions, 1):
        if args.only and i != args.only:
            continue
        trace = Trace(ROOT / "bootcamp" / "traces" / f"q{i}.jsonl")
        try:
            text = answer(question, client, tools, store, trace)
        except NotImplementedError:
            raise
        except Exception as exc:  # e.g. a rate-limit error from the provider
            trace.error(f"{type(exc).__name__}: {exc}")
            text = f"ERROR: {type(exc).__name__}: {exc}"
        print(f"Q{i}: {question}\nA{i}: {text}\n")


if __name__ == "__main__":
    main()
