"""Trace logging in the standard format: one JSON object per line (JSONL).

    trace = Trace("bootcamp/traces/q1.jsonl")
    trace.question("How many routes leave Chennai?")
    trace.llm_call(model, response_message)       # after every LLM call
    trace.tool_call("lookup_node", args, output)  # after every tool call
    trace.final_answer("23 routes leave Chennai.")

Every line has "type" and "time"; the other keys depend on the type.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


def _plain(obj: Any) -> Any:
    """Make SDK objects (pydantic models) JSON-serialisable."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump(exclude_none=True)
    return obj


class Trace:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("", encoding="utf-8")  # start a fresh trace

    def event(self, type_: str, **data: Any) -> None:
        record = {"type": type_, "time": round(time.time(), 3), **{k: _plain(v) for k, v in data.items()}}
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")

    def question(self, text: str) -> None:
        self.event("question", text=text)

    def llm_call(self, model: str, response_message: Any) -> None:
        self.event("llm_call", model=model, response=response_message)

    def tool_call(self, name: str, arguments: dict, output: dict) -> None:
        self.event("tool_call", name=name, arguments=arguments, output=output)

    def final_answer(self, text: str) -> None:
        self.event("final_answer", text=text)

    def error(self, message: str) -> None:
        self.event("error", message=message)


def read_trace(path: str | Path) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
