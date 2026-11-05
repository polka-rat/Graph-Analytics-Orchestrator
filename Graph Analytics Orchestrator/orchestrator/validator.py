"""Normalizes and validates agent responses against the course evaluation schema."""

from __future__ import annotations

import json
import re
from typing import Any

VALID_STATUSES = {"answered", "clarification_needed", "unsupported", "error"}
VALID_TYPES = {"number", "boolean", "node", "node_list", "path", "text"}


def extract_json(raw_text: str) -> dict | None:
    """Robustly extract and parse JSON from LLM text, stripping Markdown fences."""
    if not raw_text or not isinstance(raw_text, str):
        return None

    cleaned = raw_text.strip()

    # Strip markdown code blocks
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # Fallback regex extraction of outermost JSON object
    match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass

    return None


def sanitize_node_id(node_val: Any) -> str:
    """Ensure node references are clean ID strings."""
    if isinstance(node_val, dict):
        return str(node_val.get("id") or node_val.get("node") or "")
    val = str(node_val).strip()
    # Strip quotes or punctuation
    return val.strip("\"'")


def validate_and_normalize_answer(raw_payload: Any, fallback_error: str = "") -> dict:
    """Transforms raw LLM output into a certified course-compliant response dict."""
    if isinstance(raw_payload, str):
        data = extract_json(raw_payload)
    elif isinstance(raw_payload, dict):
        data = raw_payload
    else:
        data = None

    if not data or not isinstance(data, dict):
        return {
            "status": "error",
            "answer_text": fallback_error or "Failed to parse a structured JSON response from agent.",
            "answer": {"type": "text", "value": ""},
        }

    status = data.get("status", "answered")
    if status not in VALID_STATUSES:
        status = "answered"

    answer_text = str(data.get("answer_text", "")).strip()
    raw_answer = data.get("answer", {})

    if not isinstance(raw_answer, dict):
        raw_answer = {"type": "text", "value": str(raw_answer)}

    ans_type = raw_answer.get("type", "text")
    ans_val = raw_answer.get("value")

    # 1. Edge-Case Handling for Clarification and Unsupported
    if status in ("clarification_needed", "unsupported"):
        return {
            "status": status,
            "answer_text": answer_text or f"Request is {status}.",
            "answer": {"type": "text", "value": ""},
        }

    # 2. Schema Normalization for Answered Status
    if ans_type == "number":
        try:
            if isinstance(ans_val, (int, float)):
                final_val = ans_val
            else:
                cleaned_num = re.sub(r"[^\d.-]", "", str(ans_val))
                final_val = float(cleaned_num) if "." in cleaned_num else int(cleaned_num)
        except Exception:
            final_val = 0
        return {
            "status": "answered",
            "answer_text": answer_text,
            "answer": {"type": "number", "value": final_val},
        }

    if ans_type == "boolean":
        bool_val = ans_val is True or str(ans_val).lower() in ("true", "1", "yes")
        return {
            "status": "answered",
            "answer_text": answer_text,
            "answer": {"type": "boolean", "value": bool_val},
        }

    if ans_type == "node":
        return {
            "status": "answered",
            "answer_text": answer_text,
            "answer": {"type": "node", "value": sanitize_node_id(ans_val)},
        }

    if ans_type == "path":
        if isinstance(ans_val, str):
            # Parse paths formatted as "MAA -> DEL -> JFK" or comma-separated
            nodes = [sanitize_node_id(p) for p in re.split(r"\s*(?:->|→|,)\s*", ans_val) if p.strip()]
        elif isinstance(ans_val, list):
            nodes = [sanitize_node_id(p) for p in ans_val]
        else:
            nodes = []
        return {
            "status": "answered",
            "answer_text": answer_text,
            "answer": {"type": "path", "value": nodes},
        }

    if ans_type == "node_list":
        if isinstance(ans_val, str):
            nodes = [sanitize_node_id(n) for n in re.split(r"\s*,\s*", ans_val) if n.strip()]
        elif isinstance(ans_val, list):
            nodes = [sanitize_node_id(n) for n in ans_val]
        else:
            nodes = []

        res = {"type": "node_list", "value": nodes}
        if raw_answer.get("ordered"):
            res["ordered"] = True

        return {
            "status": "answered",
            "answer_text": answer_text,
            "answer": res,
        }

    return {
        "status": status,
        "answer_text": answer_text,
        "answer": {"type": "text", "value": str(ans_val or "")},
    }