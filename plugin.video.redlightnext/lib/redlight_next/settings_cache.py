from __future__ import annotations

import json
import os
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from redlight_next.core.errors import SerializationError
from redlight_next.core.serialization import dumps_json, loads_json


@dataclass(frozen=True)
class AddonSettings:
    """Typed addon settings."""

    # General
    debug_mode: bool = False
    auto_update: bool = True
    language: str = "en"

    # Providers
    real_debrid_enabled: bool = False
    real_debrid_token: str = field(default="", repr=False)
    premiumize_enabled: bool = False
    premiumize_token: str = field(default="", repr=False)
    all_debrid_enabled: bool = False
    all_debrid_token: str = field(default="", repr=False)
    torbox_enabled: bool = False
    torbox_token: str = field(default="", repr=False)
    easynews_enabled: bool = False
    easynews_user: str = ""
    easynews_password: str = field(default="", repr=False)

    # Scraping
    scraper_timeout: int = 30
    max_results: int = 50
    filter_hevc: bool = False
    filter_hdr: bool = False
    filter_dv: bool = False
    min_resolution: str = "720p"

    # Playback
    autoplay: bool = False
    source_select: bool = True
    resume_point: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AddonSettings":
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


@runtime_checkable
class CacheBackend(Protocol):
    """Protocol for cache storage backends."""

    def get(self, key: str) -> Optional[str]: ...
    def set(self, key: str, value: str, ttl: Optional[int] = None) -> None: ...
    def delete(self, key: str) -> None: ...
    def keys(self) -> List[str]: ...
    def clear(self) -> None: ...


class FileCacheBackend:
    """File-based cache backend using JSON serialization."""

    def __init__(self, directory: Path):
        self._dir = directory
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self._dir / f"{safe_key}.json"

    def get(self, key: str) -> Optional[str]:
        path = self._path(key)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                entry = json.load(f)
            if entry.get("ttl") and time.time() > entry["ttl"]:
                path.unlink()
                return None
            return entry.get("value")
        except (json.JSONDecodeError, OSError):
            return None

    def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        path = self._path(key)
        entry: Dict[str, Any] = {"value": value}
        if ttl:
            entry["ttl"] = time.time() + ttl
        with open(path, "w", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False)

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()

    def keys(self) -> List[str]:
        try:
            return [p.stem for p in self._dir.glob("*.json")]
        except OSError:
            return []

    def clear(self) -> None:
        for p in self._dir.glob("*.json"):
            try:
                p.unlink()
            except OSError:
                pass


class CacheRepository:
    """High-level cache repository with typed get/set and JSON serialization."""

    def __init__(self, backend: CacheBackend):
        self._backend = backend

    def get(self, key: str, default: Any = None) -> Any:
        raw = self._backend.get(key)
        if raw is None:
            return default
        try:
            return loads_json(raw)
        except SerializationError:
            return default

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        self._backend.set(key, dumps_json(value), ttl=ttl)

    def delete(self, key: str) -> None:
        self._backend.delete(key)

    def clear(self) -> None:
        self._backend.clear()

    def keys(self) -> List[str]:
        return self._backend.keys()
