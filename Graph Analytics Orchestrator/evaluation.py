"""Evaluate orchestrator answers against the course's structured answer rules."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


VALID_STATUSES = {
    "answered",
    "clarification_needed",
    "unsupported",
    "error",
}
MAX_TOOL_CALLS = 5


def load_json(path: str | Path) -> Any:
    """Load JSON from a path with a useful validation error."""
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _numeric_equal(expected: Any, actual: Any) -> bool:
    if isinstance(expected, bool) or isinstance(actual, bool):
        return expected == actual
    if not isinstance(expected, (int, float)) or not isinstance(actual, (int, float)):
        return False
    if not math.isfinite(expected) or not math.isfinite(actual):
        return expected == actual
    if expected == actual:
        return True
    scale = max(abs(float(expected)), 1.0)
    return abs(float(expected) - float(actual)) <= scale * 0.001


def _answer_equal(expected: dict[str, Any], actual: dict[str, Any]) -> bool:
    if not isinstance(expected, dict) or not isinstance(actual, dict):
        return False
    if expected.get("type") != actual.get("type"):
        return False

    answer_type = expected.get("type")
    expected_value = expected.get("value")
    actual_value = actual.get("value")

    if answer_type == "number":
        return _numeric_equal(expected_value, actual_value)
    if answer_type == "node_list":
        if not isinstance(expected_value, list) or not isinstance(actual_value, list):
            return False
        if expected.get("ordered", False):
            return expected_value == actual_value
        return set(expected_value) == set(actual_value)
    if answer_type in {"path", "text", "node", "boolean"}:
        return expected_value == actual_value
    return expected_value == actual_value


def _trace_summary(trace_path: Path) -> tuple[int, list[str]]:
    if not trace_path.is_file():
        return -1, []
    count = 0
    event_types = []
    with trace_path.open("r", encoding="utf-8") as file:
        for line in file:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            event_types.append(event.get("type"))
            if event.get("type") == "tool_call":
                count += 1
    return count, event_types


def evaluate(expected_results, actual_results, trace_dir=None, max_tool_calls=MAX_TOOL_CALLS):
    """Compare actual results and return a serializable evaluation report."""
    expected_by_id = {item.get("query_id"): item for item in expected_results}
    actual_by_id = {item.get("query_id"): item for item in actual_results}
    all_ids = sorted(set(expected_by_id) | set(actual_by_id))
    details = []

    for query_id in all_ids:
        expected = expected_by_id.get(query_id)
        actual = actual_by_id.get(query_id)
        failures = []

        if expected is None:
            failures.append("unexpected query_id")
        elif actual is None:
            failures.append("missing result")
        else:
            expected_status = expected.get("status")
            actual_status = actual.get("status")
            if expected_status != actual_status:
                failures.append(
                    f"status mismatch: expected {expected_status!r}, got {actual_status!r}"
                )
            elif expected_status == "answered" and not _answer_equal(
                expected.get("answer"), actual.get("answer")
            ):
                failures.append("structured answer mismatch")

        tool_calls = None
        trace_file = actual.get("trace_file") if actual else None
        if trace_dir and trace_file:
            trace_path = Path(trace_file)
            if not trace_path.is_absolute():
                trace_path = Path(trace_dir) / trace_path.name
            tool_calls, event_types = _trace_summary(trace_path)
            if tool_calls < 0:
                failures.append("missing trace file")
            else:
                if "question" not in event_types:
                    failures.append("trace missing question event")
                if "final_answer" not in event_types:
                    failures.append("trace missing final_answer event")
                if tool_calls > max_tool_calls:
                    failures.append(
                        f"tool-call limit exceeded: {tool_calls} > {max_tool_calls}"
                    )

        details.append({
            "query_id": query_id,
            "passed": not failures,
            "failures": failures,
            "tool_calls": tool_calls,
        })

    answered_expected = sum(
        item.get("status") == "answered" for item in expected_results
    )
    answered_correct = sum(
        detail["passed"]
        and expected_by_id.get(detail["query_id"], {}).get("status") == "answered"
        for detail in details
    )
    passed = sum(detail["passed"] for detail in details)
    total = len(details)

    return {
        "total_queries": total,
        "passed_queries": passed,
        "failed_queries": total - passed,
        "accuracy": passed / total if total else 0.0,
        "answered_queries": answered_expected,
        "answered_correct": answered_correct,
        "details": details,
    }


def main(argv=None):
    """Run the evaluator as ``python evaluation.py --expected ... --actual ...``."""
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected", required=True, help="Expected answers JSON")
    parser.add_argument("--actual", required=True, help="Orchestrator answers JSON")
    parser.add_argument("--traces", help="Directory containing JSONL traces")
    parser.add_argument("--out", help="Optional path for the evaluation report")
    args = parser.parse_args(argv)

    expected = load_json(args.expected)
    actual = load_json(args.actual)
    if not isinstance(expected, list) or not isinstance(actual, list):
        raise ValueError("Expected and actual answer files must contain JSON lists.")

    report = evaluate(expected, actual, args.traces)
    text = json.dumps(report, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
