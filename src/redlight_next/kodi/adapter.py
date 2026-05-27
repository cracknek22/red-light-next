from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol, Tuple, runtime_checkable


@dataclass(frozen=True)
class ListItemInfo:
    """Kodi list item metadata."""

    title: str
    mediatype: str = "video"
    year: Optional[int] = None
    genre: Optional[str] = None
    plot: Optional[str] = None
    rating: Optional[float] = None
    duration: Optional[int] = None
    cast: List[str] = field(default_factory=list)
    director: Optional[str] = None
    writer: Optional[str] = None
    mpaa: Optional[str] = None
    trailer: Optional[str] = None
    playcount: int = 0


@dataclass(frozen=True)
class Artwork:
    poster: Optional[str] = None
    fanart: Optional[str] = None
    thumb: Optional[str] = None
    banner: Optional[str] = None
    clearlogo: Optional[str] = None


@dataclass(frozen=True)
class KodiListItem:
    """Pure data representation of a Kodi list item."""

    label: str
    path: Optional[str] = None
    is_folder: bool = True
    info: Optional[ListItemInfo] = None
    artwork: Optional[Artwork] = None
    context_menu: List[Tuple[str, str]] = field(default_factory=list)
    properties: Dict[str, str] = field(default_factory=dict)


@runtime_checkable
class KodiInterface(Protocol):
    """Protocol for Kodi runtime interface."""

    def add_directory_item(self, item: KodiListItem) -> bool: ...
    def end_of_directory(self, succeeded: bool = True) -> None: ...
    def set_content(self, content: str) -> None: ...
    def resolve_url(self, url: str, succeeded: bool = True) -> None: ...
    def notify(self, title: str, message: str, duration_ms: int = 3000) -> None: ...
    def addon_id(self) -> str: ...
    def addon_name(self) -> str: ...
    def addon_path(self) -> str: ...
    def get_setting(self, key: str, default: str = "") -> str: ...
    def set_setting(self, key: str, value: str) -> None: ...
    def open_settings(self) -> None: ...
    def get_user_input(self, heading: str, default: str = "") -> Optional[str]: ...
    def select_dialog(self, heading: str, options: List[str]) -> Optional[int]: ...
    def container_refresh(self) -> None: ...
    def get_keyboard_input(self, heading: str, hidden: bool = False, default: str = "") -> Optional[str]: ...


class BaseKodiAdapter(ABC):
    """Abstract base for Kodi adapter implementations."""

    def build_url(self, mode: str, **kwargs: Optional[str]) -> str:
        """Build a plugin:// URL for a given mode."""
        params = "&".join(f"{k}={v}" for k, v in kwargs.items() if v is not None)
        sep = "&" if params else ""
        return f"plugin://{self.addon_id()}/?mode={mode}{sep}{params}"

    @abstractmethod
    def add_directory_item(self, item: KodiListItem) -> bool: ...

    @abstractmethod
    def end_of_directory(self, succeeded: bool = True) -> None: ...

    @abstractmethod
    def set_content(self, content: str) -> None: ...

    @abstractmethod
    def resolve_url(self, url: str, succeeded: bool = True) -> None: ...

    @abstractmethod
    def notify(self, title: str, message: str, duration_ms: int = 3000) -> None: ...

    @abstractmethod
    def addon_id(self) -> str: ...

    @abstractmethod
    def addon_name(self) -> str: ...

    @abstractmethod
    def addon_path(self) -> str: ...

    @abstractmethod
    def get_setting(self, key: str, default: str = "") -> str: ...

    @abstractmethod
    def set_setting(self, key: str, value: str) -> None: ...

    @abstractmethod
    def open_settings(self) -> None: ...

    @abstractmethod
    def get_user_input(self, heading: str, default: str = "") -> Optional[str]: ...

    @abstractmethod
    def select_dialog(self, heading: str, options: List[str]) -> Optional[int]: ...

    @abstractmethod
    def container_refresh(self) -> None: ...

    @abstractmethod
    def get_keyboard_input(self, heading: str, hidden: bool = False, default: str = "") -> Optional[str]: ...
