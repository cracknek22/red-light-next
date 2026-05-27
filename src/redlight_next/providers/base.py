from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


class ProviderStatus(Enum):
    OK = "ok"
    AUTH_ERROR = "auth_error"
    RATE_LIMITED = "rate_limited"
    UNAVAILABLE = "unavailable"
    DISABLED = "disabled"


@dataclass(frozen=True)
class ResolvedLink:
    """A resolved stream/download link from a provider."""

    url: str
    quality: str = "unknown"
    size_bytes: Optional[int] = None
    filename: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderHealth:
    status: ProviderStatus
    message: str = ""
    quota_info: Optional[Dict[str, Any]] = None


@runtime_checkable
class DebridProvider(Protocol):
    """Protocol for debrid/premium link resolver providers."""

    @property
    def name(self) -> str: ...

    @property
    def enabled(self) -> bool: ...

    def health(self) -> ProviderHealth: ...

    def resolve(self, magnet_or_url: str) -> List[ResolvedLink]: ...

    def unrestrict(self, url: str) -> ResolvedLink: ...


class BaseDebridProvider(ABC):
    """Abstract base for debrid providers with common logic."""

    def __init__(self, token: str, enabled: bool = True, timeout: int = 30):
        self._token = token
        self._enabled = enabled and bool(token)
        self._timeout = timeout

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @property
    def enabled(self) -> bool:
        return self._enabled

    @abstractmethod
    def health(self) -> ProviderHealth:
        ...

    @abstractmethod
    def resolve(self, magnet_or_url: str) -> List[ResolvedLink]:
        ...

    @abstractmethod
    def unrestrict(self, url: str) -> ResolvedLink:
        ...

    def _auth_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}
