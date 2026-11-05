"""Talking to an LLM through an OpenAI-compatible API.

Gemini, Groq, OpenRouter and Ollama all accept the OpenAI API format, so one
client works with any of them. Configure it with environment variables
(or a .env file; see .env.example):

    LLM_API_KEY   your key (for Ollama any non-empty string)
    LLM_BASE_URL  default: Gemini, https://generativelanguage.googleapis.com/v1beta/openai/
    LLM_MODEL     default: gemini-3.8-flash
"""
from __future__ import annotations

import copy
import os

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
DEFAULT_MODEL = "gemini-3.8-flash"

# JSON-schema keys that every provider accepts. Others (default, maximum, ...)
# are moved into the description, because some providers reject them.
_SCHEMA_KEYS = {"type", "description", "properties", "required", "items", "enum"}


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


def model_name() -> str:
    _load_dotenv()
    return os.environ.get("LLM_MODEL", DEFAULT_MODEL)


def make_client():
    """An openai.OpenAI client pointed at the configured provider."""
    _load_dotenv()
    from openai import OpenAI

    key = os.environ.get("LLM_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("Set LLM_API_KEY (see .env.example). Never put the key in your code.")
    return OpenAI(api_key=key, base_url=os.environ.get("LLM_BASE_URL", GEMINI_BASE_URL))


def _clean_schema(schema: dict) -> dict:
    out = {}
    extras = []
    for key, value in schema.items():
        if key in _SCHEMA_KEYS:
            out[key] = value
        else:
            extras.append(f"{key}: {value}")
    if "properties" in out:
        out["properties"] = {k: _clean_schema(v) for k, v in out["properties"].items()}
    if "items" in out and isinstance(out["items"], dict):
        out["items"] = _clean_schema(out["items"])
    if extras:
        out["description"] = (out.get("description", "") + f" ({'; '.join(extras)})").strip()
    return out


def tool_schema(manifest: dict) -> dict:
    """Turn a tool manifest into the 'tools' entry of an OpenAI-style chat request."""
    params = _clean_schema(copy.deepcopy(manifest["parameters"]))
    return {"type": "function",
            "function": {"name": manifest["name"], "description": manifest["description"], "parameters": params}}
