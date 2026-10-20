"""Local, data-only session checkpoints for Agent 003.

No tool calls, proposals, approvals, API keys, or recovery capabilities are
serialized by this module. The caller must supply only non-sensitive summaries.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1
MAX_EVENTS = 100
MAX_SUMMARY_CHARS = 500
VALID_KINDS = {"user_summary", "agent_summary", "task_outcome", "session_note"}


class SessionDataError(ValueError):
    """Session data is invalid or cannot safely be loaded."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_session() -> dict:
    return {"schema_version": SCHEMA_VERSION, "created_at": _now(),
            "updated_at": _now(), "events": []}


def _validate(state: object) -> dict:
    if not isinstance(state, dict) or set(state) != {"schema_version", "created_at", "updated_at", "events"}:
        raise SessionDataError("Unexpected session structure")
    if state["schema_version"] != SCHEMA_VERSION:
        raise SessionDataError("Unsupported session schema version")
    if not all(isinstance(state[key], str) and len(state[key]) <= 80 for key in ("created_at", "updated_at")):
        raise SessionDataError("Invalid timestamps")
    events = state["events"]
    if not isinstance(events, list) or len(events) > MAX_EVENTS:
        raise SessionDataError("Invalid event count")
    for event in events:
        if (not isinstance(event, dict) or set(event) != {"kind", "summary", "timestamp"}
                or event["kind"] not in VALID_KINDS
                or not isinstance(event["summary"], str)
                or len(event["summary"]) > MAX_SUMMARY_CHARS
                or not isinstance(event["timestamp"], str)
                or len(event["timestamp"]) > 80):
            raise SessionDataError("Invalid event")
    return state


def append_summary(state: dict, kind: str, summary: str) -> dict:
    """Return a validated new state containing a bounded, data-only event."""
    _validate(state)
    if kind not in VALID_KINDS or not isinstance(summary, str) or len(summary) > MAX_SUMMARY_CHARS:
        raise SessionDataError("Invalid event summary")
    updated = {**state, "updated_at": _now(),
               "events": [*state["events"], {"kind": kind, "summary": summary, "timestamp": _now()}][-MAX_EVENTS:]}
    return _validate(updated)


def load_session(path: str | Path) -> dict:
    """Missing file starts a new session; invalid data raises (never silently resets)."""
    path = Path(path)
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return new_session()
    except OSError as exc:
        raise SessionDataError(f"Cannot read session: {type(exc).__name__}") from exc
    try:
        return _validate(json.loads(raw))
    except (ValueError, TypeError) as exc:
        raise SessionDataError("Session file is invalid; preserved for inspection") from exc


def save_session(path: str | Path, state: dict) -> None:
    """Write a validated checkpoint via same-directory temporary file + replace."""
    _validate(state)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=f".{path.name}.", suffix=".tmp",
                                         delete=False) as handle:
            temp_name = handle.name
            json.dump(state, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if temp_name is not None:
            try:
                Path(temp_name).unlink(missing_ok=True)
            except OSError:
                pass
