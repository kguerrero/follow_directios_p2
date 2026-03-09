"""Render conversational instructions from a JSON question bank."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

QUESTIONS_DIR = Path(__file__).resolve().parents[1] / "config" / "questions"


@lru_cache(maxsize=1)
def _load_bank() -> dict[str, Any]:
    if not QUESTIONS_DIR.exists():
        raise FileNotFoundError(f"Question bank directory not found: {QUESTIONS_DIR}")
    bank: dict[str, Any] = {}
    for path in sorted(QUESTIONS_DIR.glob("*.json")):
        with path.open("r", encoding="utf-8") as fh:
            bank[path.stem] = json.load(fh)
    if not bank:
        raise FileNotFoundError(f"No question files found in {QUESTIONS_DIR}")
    return bank


def _get_tool_entry(tool_key: str) -> dict[str, Any]:
    bank = _load_bank()
    try:
        return bank[tool_key]
    except KeyError as exc:  # pragma: no cover - defensive; enforced by tests
        raise KeyError(f"Unknown tool key '{tool_key}'. Available: {sorted(bank)}") from exc


def _label(required: bool | None) -> str:
    return "required" if required else "optional"


def _escape_quotes(text: str) -> str:
    return text.replace('"', r'\"')


def _format_validation(validation: Any) -> str | None:
    if validation is None:
        return None
    if isinstance(validation, str):
        return validation
    if isinstance(validation, dict):
        items = ", ".join(f"{key}={value}" for key, value in validation.items())
        return items
    return str(validation)


def _iter_questions(question_block: dict[str, Any]) -> Iterable[str]:
    bullet_indent: str = question_block.get("bullet_indent", "")
    for question in question_block.get("questions", []):
        base = f"{question['id']} ({_label(question.get('required'))})"
        segments: list[str] = []
        prompt = question.get("prompt")
        if prompt:
            segments.append(f"ask: \"{_escape_quotes(prompt)}\"")
        validation_text = _format_validation(question.get("validation"))
        if validation_text:
            segments.append(f"validation: {validation_text}")
        notes = question.get("notes")
        if notes:
            segments.append(f"notes: {notes}")
        if segments:
            base = f"{base} " + "; ".join(segments)
        yield f"{bullet_indent}- {base}"


def format_question_collection(
    tool_key: str,
    *,
    heading: str | None = None,
    heading_indent: str = "",
    bullet_indent: str = "",
) -> str:
    """Return a formatted requirements block for the tool's question list."""
    entry = _get_tool_entry(tool_key)
    collection = entry.get("collection", {})
    questions_block = dict(collection)
    questions_block["bullet_indent"] = bullet_indent
    heading_text = heading or collection.get("default_heading")

    lines: list[str] = []
    if heading_text:
        lines.append(f"{heading_indent}{heading_text}")
    lines.extend(_iter_questions(questions_block))
    return "\n".join(lines)


def format_confirmation_checklist(
    tool_key: str,
    *,
    heading: str | None = None,
    heading_indent: str = "",
    bullet_indent: str = "",
    closing_line: str | None = None,
) -> str:
    """Return confirmation text derived from the JSON bank."""
    entry = _get_tool_entry(tool_key)
    confirmation = entry.get("confirmation", {})
    heading_text = heading or confirmation.get("default_heading")
    closing = confirmation.get("default_closing_line")
    if closing_line is not None:
        closing = closing_line

    lines: list[str] = []
    if heading_text:
        lines.append(f"{heading_indent}{heading_text}")
    for item in confirmation.get("items", []):
        prompt = item.get("prompt", "")
        lines.append(
            f"{bullet_indent}- Confirm {item['id']} ({_label(item.get('required'))}): {prompt}"
        )
    if closing:
        lines.append(f"{heading_indent}{closing}")
    return "\n".join(lines)
