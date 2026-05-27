from __future__ import annotations

import logging
from typing import Optional

from redlight_next.security.redaction import redact_secrets

LOGGER_NAME = "redlight_next"


def get_logger(name: Optional[str] = None) -> logging.Logger:
    suffix = f".{name}" if name else ""
    return logging.getLogger(f"{LOGGER_NAME}{suffix}")


def log_exception(component: str, action: str, exc: Exception) -> None:
    logger = get_logger(component)
    safe_message = redact_secrets(f"{type(exc).__name__}: {exc}")
    logger.exception("%s failed: %s", action, safe_message)


def configure_basic_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
