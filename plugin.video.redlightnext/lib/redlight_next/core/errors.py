from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


class RedLightNextError(Exception):
    """Base exception for Red Light Next."""


@dataclass(frozen=True)
class ErrorContext:
    component: str
    action: str
    message: str
    cause: Optional[str] = None

    def format(self) -> str:
        suffix = f" cause={self.cause}" if self.cause else ""
        return f"{self.component}.{self.action}: {self.message}{suffix}"


class RouteNotFoundError(RedLightNextError):
    pass


class SerializationError(RedLightNextError):
    pass


class HTTPClientError(RedLightNextError):
    pass


class UnsafeArchiveError(RedLightNextError):
    pass


class ProviderError(RedLightNextError):
    pass
