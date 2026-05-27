from unittest.mock import MagicMock

import pytest

from redlight_next.core.http import HTTPClient, HTTPResponse
from redlight_next.core.errors import ProviderError
from redlight_next.providers.base import ProviderHealth, ProviderStatus, ResolvedLink
from redlight_next.providers.real_debrid import RealDebridProvider
from redlight_next.providers.registry import ProviderRegistry


class FakeHTTPClient:
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        key = (method, url)
        if key in self.responses:
            return self.responses[key]
        return HTTPResponse(status_code=200, text='{}', content=b'{}', headers={})

    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self.request("POST", url, **kwargs)


class TestRealDebridProvider:
    def test_disabled_without_token(self):
        p = RealDebridProvider(token="")
        assert p.enabled is False

    def test_health_ok(self):
        client = FakeHTTPClient({
            ("GET", "https://api.real-debrid.com/rest/1.0/user"):
                HTTPResponse(status_code=200, text='{"premium": 1, "username": "test"}', content=b'{"premium": 1, "username": "test"}', headers={}),
        })
        p = RealDebridProvider(token="valid", client=client)
        health = p.health()
        assert health.status == ProviderStatus.OK
        assert health.quota_info == {"premium": 1, "username": "test"}

    def test_health_auth_error(self):
        client = FakeHTTPClient({
            ("GET", "https://api.real-debrid.com/rest/1.0/user"):
                HTTPResponse(status_code=401, text='{"error": "bad_token"}', content=b'{"error": "bad_token"}', headers={}),
        })
        p = RealDebridProvider(token="bad", client=client)
        health = p.health()
        assert health.status == ProviderStatus.AUTH_ERROR

    def test_resolve_magnet(self):
        client = FakeHTTPClient({
            ("POST", "https://api.real-debrid.com/rest/1.0/torrents/addMagnet"):
                HTTPResponse(status_code=201, text='{"id": "abc123"}', content=b'{"id": "abc123"}', headers={}),
            ("GET", "https://api.real-debrid.com/rest/1.0/torrents/info/abc123"):
                HTTPResponse(status_code=200, text='{"links": ["http://link1"]}', content=b'{"links": ["http://link1"]}', headers={}),
            ("POST", "https://api.real-debrid.com/rest/1.0/unrestrict/link"):
                HTTPResponse(status_code=200, text='{"download": "http://file.mkv", "filename": "movie.mkv", "filesize": 1024}', content=b'{"download": "http://file.mkv", "filename": "movie.mkv", "filesize": 1024}', headers={}),
        })
        p = RealDebridProvider(token="valid", client=client)
        links = p.resolve("magnet:?xt=urn:btih:abc")
        assert len(links) == 1
        assert links[0].url == "http://file.mkv"
        assert links[0].filename == "movie.mkv"

    def test_resolve_direct_link(self):
        client = FakeHTTPClient({
            ("POST", "https://api.real-debrid.com/rest/1.0/unrestrict/link"):
                HTTPResponse(status_code=200, text='{"download": "http://file.mkv", "filename": "movie.mkv"}', content=b'{"download": "http://file.mkv", "filename": "movie.mkv"}', headers={}),
        })
        p = RealDebridProvider(token="valid", client=client)
        links = p.resolve("http://host.com/file")
        assert len(links) == 1
        assert links[0].url == "http://file.mkv"

    def test_unrestrict(self):
        client = FakeHTTPClient({
            ("POST", "https://api.real-debrid.com/rest/1.0/unrestrict/link"):
                HTTPResponse(status_code=200, text='{"download": "http://file.mkv", "filename": "movie.mkv", "filesize": 2048}', content=b'{"download": "http://file.mkv", "filename": "movie.mkv", "filesize": 2048}', headers={}),
        })
        p = RealDebridProvider(token="valid", client=client)
        link = p.unrestrict("http://restricted.com")
        assert link.url == "http://file.mkv"
        assert link.size_bytes == 2048

    def test_disabled_resolve_returns_empty(self):
        p = RealDebridProvider(token="", enabled=False)
        assert p.resolve("magnet:?xt=urn:btih:abc") == []

    def test_disabled_unrestrict_raises(self):
        p = RealDebridProvider(token="", enabled=False)
        with pytest.raises(ProviderError):
            p.unrestrict("http://restricted.com")


class TestProviderRegistry:
    def test_register_and_get(self):
        reg = ProviderRegistry()
        p = RealDebridProvider(token="abc")
        reg.register(p)
        assert reg.get("RealDebridProvider") is p

    def test_list_enabled(self):
        class OtherProvider(RealDebridProvider):
            pass
        reg = ProviderRegistry()
        reg.register(RealDebridProvider(token="abc"))
        reg.register(OtherProvider(token="", enabled=False))
        enabled = reg.list_enabled()
        assert len(enabled) == 1
        assert isinstance(enabled[0], RealDebridProvider)

    def test_health_summary(self):
        reg = ProviderRegistry()
        reg.register(RealDebridProvider(token="abc"))
        summary = reg.health_summary()
        assert "RealDebridProvider" in summary

    def test_resolve_first_falls_back(self):
        class DummyProvider(RealDebridProvider):
            pass
        reg = ProviderRegistry()
        reg.register(DummyProvider(token="", enabled=False))  # disabled
        assert reg.resolve_first("magnet:?xt=urn:btih:abc") is None

    def test_resolve_first_success(self):
        client = FakeHTTPClient({
            ("POST", "https://api.real-debrid.com/rest/1.0/torrents/addMagnet"):
                HTTPResponse(status_code=201, text='{"id": "abc"}', content='{"id": "abc"}'.encode('utf-8'), headers={}),
            ("GET", "https://api.real-debrid.com/rest/1.0/torrents/info/abc"):
                HTTPResponse(status_code=200, text='{"links": ["http://link1"]}', content='{"links": ["http://link1"]}'.encode('utf-8'), headers={}),
            ("POST", "https://api.real-debrid.com/rest/1.0/unrestrict/link"):
                HTTPResponse(status_code=200, text='{"download": "http://file.mkv", "filename": "movie.mkv"}', content='{"download": "http://file.mkv", "filename": "movie.mkv"}'.encode('utf-8'), headers={}),
        })
        reg = ProviderRegistry()
        reg.register(RealDebridProvider(token="abc", client=client))
        link = reg.resolve_first("magnet:?xt=urn:btih:abc")
        assert link is not None
        assert link.url == "http://file.mkv"
