from __future__ import annotations

import ast
import json
from typing import Any

from redlight_next.core.errors import SerializationError


def dumps_json(value: Any) -> str:
    """Serialize cache data as deterministic JSON only."""
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError) as exc:
        raise SerializationError(f"Value is not JSON serializable: {type(value).__name__}") from exc


def loads_json(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise SerializationError("Invalid JSON payload") from exc


def migrate_legacy_literal(value: str) -> Any:
    """Safely read old Python-literal cache data without using eval()."""
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError) as exc:
        raise SerializationError("Invalid legacy literal payload") from exc
