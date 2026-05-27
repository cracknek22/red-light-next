import json
import os
import time
from pathlib import Path

import pytest

from redlight_next.settings_cache import (
    AddonSettings,
    CacheRepository,
    FileCacheBackend,
)


class TestAddonSettings:
    def test_default_values(self):
        s = AddonSettings()
        assert s.debug_mode is False
        assert s.auto_update is True
        assert s.language == "en"
        assert s.scraper_timeout == 30
        assert s.max_results == 50
        assert s.real_debrid_enabled is False
        assert s.real_debrid_token == ""

    def test_custom_values(self):
        s = AddonSettings(debug_mode=True, language="nl", scraper_timeout=60)
        assert s.debug_mode is True
        assert s.language == "nl"
        assert s.scraper_timeout == 60

    def test_to_dict_roundtrip(self):
        s = AddonSettings(debug_mode=True, real_debrid_token="secret123")
        d = s.to_dict()
        assert d["debug_mode"] is True
        assert d["real_debrid_token"] == "secret123"
        restored = AddonSettings.from_dict(d)
        assert restored == s

    def test_from_dict_ignores_unknown_keys(self):
        d = {"debug_mode": True, "unknown_key": "ignored"}
        s = AddonSettings.from_dict(d)
        assert s.debug_mode is True
        assert not hasattr(s, "unknown_key")

    def test_repr_hides_secrets(self):
        s = AddonSettings(real_debrid_token="secret")
        r = repr(s)
        assert "secret" not in r


class TestFileCacheBackend:
    def test_get_missing_returns_none(self, tmp_path):
        backend = FileCacheBackend(tmp_path)
        assert backend.get("missing") is None

    def test_set_and_get(self, tmp_path):
        backend = FileCacheBackend(tmp_path)
        backend.set("key1", "value1")
        assert backend.get("key1") == "value1"

    def test_delete(self, tmp_path):
        backend = FileCacheBackend(tmp_path)
        backend.set("key1", "value1")
        backend.delete("key1")
        assert backend.get("key1") is None

    def test_ttl_expires(self, tmp_path):
        backend = FileCacheBackend(tmp_path)
        backend.set("key1", "value1", ttl=1)
        assert backend.get("key1") == "value1"
        time.sleep(1.1)
        assert backend.get("key1") is None

    def test_keys(self, tmp_path):
        backend = FileCacheBackend(tmp_path)
        backend.set("a", "1")
        backend.set("b", "2")
        assert sorted(backend.keys()) == ["a", "b"]

    def test_clear(self, tmp_path):
        backend = FileCacheBackend(tmp_path)
        backend.set("a", "1")
        backend.clear()
        assert backend.get("a") is None
        assert backend.keys() == []

    def test_safe_key_names(self, tmp_path):
        backend = FileCacheBackend(tmp_path)
        backend.set("path/to/key", "value")
        assert backend.get("path/to/key") == "value"


class TestCacheRepository:
    def test_get_set_json(self, tmp_path):
        backend = FileCacheBackend(tmp_path)
        repo = CacheRepository(backend)
        repo.set("data", {"list": [1, 2, 3]})
        assert repo.get("data") == {"list": [1, 2, 3]}

    def test_get_default(self, tmp_path):
        backend = FileCacheBackend(tmp_path)
        repo = CacheRepository(backend)
        assert repo.get("missing", "default") == "default"

    def test_delete_and_clear(self, tmp_path):
        backend = FileCacheBackend(tmp_path)
        repo = CacheRepository(backend)
        repo.set("a", 1)
        repo.set("b", 2)
        repo.delete("a")
        assert repo.get("a") is None
        assert repo.get("b") == 2
        repo.clear()
        assert repo.get("b") is None

    def test_ttl(self, tmp_path):
        backend = FileCacheBackend(tmp_path)
        repo = CacheRepository(backend)
        repo.set("temp", "value", ttl=1)
        assert repo.get("temp") == "value"
        time.sleep(1.1)
        assert repo.get("temp") is None
