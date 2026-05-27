from __future__ import annotations

import re
from typing import Iterable

_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)(api[_-]?key|token|secret|password)(\s*[:=]\s*)(['\"]?)[^\s'\"]{6,}(['\"]?)"
)
_SECRET_PATTERNS = [
    re.compile(r"(?i)Bearer\s+[A-Za-z0-9._~+/=-]{10,}"),
    re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}\b"),
]


def _mask_assignment(match: re.Match[str]) -> str:
    key, sep, quote, _end_quote = match.group(1), match.group(2), match.group(3), match.group(4)
    return f"{key}{sep}{quote}***REDACTED***{quote}"


def redact_secrets(text: object, extra_patterns: Iterable[re.Pattern[str]] = ()) -> str:
    """Return text with common tokens/API keys masked."""
    value = str(text)
    value = _ASSIGNMENT_PATTERN.sub(_mask_assignment, value)
    patterns = list(_SECRET_PATTERNS) + list(extra_patterns)
    for pattern in patterns:
        value = pattern.sub("***REDACTED***", value)
    return value
