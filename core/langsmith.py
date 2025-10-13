# core/langsmith.py
from typing import Optional, Dict, Any
import os


def is_enabled() -> bool:
    # Support either LangSmith legacy or LangChain unified env vars
    return bool(os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY"))


def status_badge() -> str:
    return "🟢 LangSmith Connected" if is_enabled() else "⚪ LangSmith Off"


def trace(event: str, payload: Optional[Dict[str, Any]] = None):
    # Minimal, safe no-op if not configured
    if not is_enabled():
        return
    try:
        # Minimal structured log to stdout so LangSmith proxy tools can pick it up if present
        line = {"event": event, "payload": payload or {}}
        print(f"[LANGSMITH] {line}")
    except Exception:
        pass
