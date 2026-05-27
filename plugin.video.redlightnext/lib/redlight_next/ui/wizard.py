from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Tuple, runtime_checkable


class DiagnosticStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"


@dataclass(frozen=True)
class DiagnosticResult:
    component: str
    status: DiagnosticStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


class DiagnosticCheck(Protocol):
    def name(self) -> str: ...
    def run(self) -> DiagnosticResult: ...


class SetupWizard:
    """Multi-step setup wizard for initial configuration."""

    STEPS = [
        "welcome",
        "language",
        "providers",
        "scraper_settings",
        "playback",
        "complete",
    ]

    def __init__(self, adapter: Any):
        self._adapter = adapter
        self._settings: Dict[str, Any] = {}
        self._current_step = 0

    @property
    def step(self) -> int:
        return self._current_step

    @property
    def step_name(self) -> str:
        return self.STEPS[self._current_step]

    def is_complete(self) -> bool:
        return self._current_step >= len(self.STEPS) - 1

    def next(self) -> str:
        if not self.is_complete():
            self._current_step += 1
        return self.step_name

    def prev(self) -> str:
        if self._current_step > 0:
            self._current_step -= 1
        return self.step_name

    def set_value(self, key: str, value: Any) -> None:
        self._settings[key] = value

    def get_value(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)

    def get_all_settings(self) -> Dict[str, Any]:
        return dict(self._settings)


@dataclass(frozen=True)
class ProviderBadge:
    """Badge shown next to a source result."""

    label: str
    color: str = "white"
    icon: Optional[str] = None


@dataclass(frozen=True)
class SourceResult:
    """A scraped source result with metadata for display."""

    title: str
    provider: str
    quality: str
    size_label: str
    codec: Optional[str] = None
    has_hdr: bool = False
    has_dv: bool = False
    badges: List[ProviderBadge] = field(default_factory=list)
    url: Optional[str] = None
    debrid_only: bool = False
    seeds: Optional[int] = None


@dataclass(frozen=True)
class NoResultsDiagnosis:
    """Diagnosis info when no results are found."""

    query: str
    checked_providers: List[str]
    active_filters: Dict[str, Any]
    suggestions: List[str] = field(default_factory=list)
    provider_errors: Dict[str, str] = field(default_factory=dict)

    def has_provider_errors(self) -> bool:
        return bool(self.provider_errors)

    def format_message(self) -> str:
        lines = [f"No results found for: {self.query}"]
        if self.provider_errors:
            lines.append("Provider errors:")
            for provider, error in self.provider_errors.items():
                lines.append(f"  - {provider}: {error}")
        if self.active_filters:
            lines.append(f"Active filters: {self.active_filters}")
        if self.suggestions:
            lines.append("Suggestions:")
            for suggestion in self.suggestions:
                lines.append(f"  - {suggestion}")
        return "\n".join(lines)


@dataclass(frozen=True)
class MenuItem:
    """UI contract: a single menu item the Kodi adapter should render."""

    label: str
    action: str
    is_folder: bool = True
    icon: Optional[str] = None
    fanart: Optional[str] = None
    description: Optional[str] = None
    properties: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class MenuPage:
    """UI contract: a full page of menu items."""

    title: str
    items: List[MenuItem]
    content_type: str = "videos"
    sort_methods: List[str] = field(default_factory=lambda: ["label"])
