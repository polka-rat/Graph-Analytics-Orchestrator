
"""Main entry point for the Graph Analytics Orchestrator."""

import argparse
import json
import sys
from pathlib import Path

from graphkit import GraphStore
from graphkit.llm import make_client
from graphkit.trace import Trace

from orchestrator.planner import Planner
from orchestrator.workflow import build_workflow
from orchestrator.answer_parser import parse_answer


MAX_TOOL_CALLS = 5



def recover_tools_used(trace_path, planner):
    """Recover successfully executed tools from a query's trace."""

    tools = planner.get_tools()
    recovered = []

    if not trace_path.exists():
        return recovered

    with trace_path.open("r", encoding="utf-8") as file:
        for line in file:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            if event.get("type") != "tool_call":
                continue

            output = event.get("output", {})

            # Include only successfully executed tools.
            if output.get("status") != "ok":
                continue

            tool_name = event.get("name")
            tool = tools.get(tool_name)

            if tool is not None:
                recovered.append(tool.implementation_id)

    return recovered


def load_queries(query_file):
    """Load and validate questions from a JSON file."""

    path = Path(query_file)

    if not path.exists():
        raise FileNotFoundError(f"Query file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        queries = json.load(file)

    if not isinstance(queries, list):
        raise ValueError("Query file must contain a JSON list.")

    seen_ids = set()

    for index, item in enumerate(queries):
        if not isinstance(item, dict):
            raise ValueError(f"Query at index {index} must be an object.")

        query_id = item.get("query_id")
        query = item.get("query")

        if not isinstance(query_id, str) or not query_id.strip():
            raise ValueError(f"Query at index {index} has no valid query_id.")

        if query_id in seen_ids:
            raise ValueError(f"Duplicate query_id: {query_id}")

        if not isinstance(query, str) or not query.strip():
            raise ValueError(f"Query {query_id} has no valid query text.")

        seen_ids.add(query_id)

    return queries


def process_query(item, planner, store, client, trace_dir):
    """Execute one question through the LangGraph workflow."""

    query_id = item["query_id"]
    question = item["query"]

    trace_path = trace_dir / f"{query_id}.jsonl"
    trace = Trace(trace_path)
    trace.question(question)

    try:
        system_prompt = planner.get_system_prompt(store)

        workflow = build_workflow(
            client,
            planner,
            store,
            trace,
        )

        initial_state = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            "question": question,
            "tool_calls_count": 0,
            "max_tool_calls": MAX_TOOL_CALLS,
            "tools_used": [],
            "answer_text": "",
            "answer": None,
            "status": "running",
            "error": None,
        }

        final_state = workflow.invoke(initial_state)

        raw_answer = final_state.get("answer_text", "")
        parsed = parse_answer(raw_answer)

        # Preserve explicit workflow errors.
        if final_state.get("status") == "error":
            parsed["status"] = "error"

            if final_state.get("error"):
                parsed["answer_text"] = final_state["error"]

        result = {
            "query_id": query_id,
            "status": parsed["status"],
            "answer_text": parsed["answer_text"],
            "answer": parsed["answer"],
            "tools_used": final_state.get("tools_used", []),
            "trace_file": trace_path.as_posix(),
        }

        trace.final_answer(result["answer_text"])

        return result

    except Exception as exc:
        message = str(exc)

        # Recover tools that executed successfully before the error.
        tools_used = recover_tools_used(trace_path, planner)

        trace.error(message)
        trace.final_answer(message)

        return {
            "query_id": query_id,
            "status": "error",
            "answer_text": message,
            "answer": {
                "type": "text",
                "value": message,
            },
            "tools_used": tools_used,
            "trace_file": trace_path.as_posix(),
        }


def main():
    parser = argparse.ArgumentParser(
        description="Graph Analytics Orchestrator"
    )

    parser.add_argument(
        "--queries",
        required=True,
        help="Path to the JSON query file.",
    )

    parser.add_argument(
        "--out",
        required=True,
        help="Path to the output JSON file.",
    )

    args = parser.parse_args()

    try:
        queries = load_queries(args.queries)

        # Initialize shared components only once.
        planner = Planner()
        store = GraphStore()
        client = make_client()

        trace_dir = Path("traces")
        trace_dir.mkdir(parents=True, exist_ok=True)

        results = []

        for item in queries:
            result = process_query(
                item,
                planner,
                store,
                client,
                trace_dir,
            )

            results.append(result)

            print(
                f"[{result['status'].upper()}] "
                f"{result['query_id']}: {result['answer_text']}"
            )

        output_path = Path(args.out)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8") as file:
            json.dump(
                results,
                file,
                indent=4,
                ensure_ascii=False,
            )

        print(f"\nProcessed {len(results)} queries.")
        print(f"Output saved to: {output_path}")

    except Exception as exc:
        print(f"Orchestrator error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
