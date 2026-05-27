import pytest

from redlight_next.providers.base import (
    BaseDebridProvider,
    DebridProvider,
    ProviderHealth,
    ProviderStatus,
    ResolvedLink,
)


class FakeProvider(BaseDebridProvider):
    def health(self):
        return ProviderHealth(status=ProviderStatus.OK)

    def resolve(self, magnet_or_url):
        return [ResolvedLink(url="http://example.com/file.mkv", quality="1080p")]

    def unrestrict(self, url):
        return ResolvedLink(url=url, quality="1080p")


class TestResolvedLink:
    def test_defaults(self):
        link = ResolvedLink(url="http://example.com")
        assert link.quality == "unknown"
        assert link.size_bytes is None
        assert link.filename is None
        assert link.headers == {}

    def test_full(self):
        link = ResolvedLink(
            url="http://example.com",
            quality="4K",
            size_bytes=1024,
            filename="movie.mkv",
            headers={"Range": "bytes=0-"},
        )
        assert link.quality == "4K"
        assert link.size_bytes == 1024


class TestProviderHealth:
    def test_defaults(self):
        h = ProviderHealth(status=ProviderStatus.OK)
        assert h.message == ""
        assert h.quota_info is None


class TestBaseDebridProvider:
    def test_name(self):
        p = FakeProvider(token="abc")
        assert p.name == "FakeProvider"

    def test_enabled_with_token(self):
        p = FakeProvider(token="abc")
        assert p.enabled is True

    def test_enabled_without_token(self):
        p = FakeProvider(token="")
        assert p.enabled is False

    def test_enabled_explicit_false(self):
        p = FakeProvider(token="abc", enabled=False)
        assert p.enabled is False

    def test_auth_headers(self):
        p = FakeProvider(token="secret")
        assert p._auth_headers()["Authorization"] == "Bearer secret"

    def test_isinstance_protocol(self):
        p = FakeProvider(token="abc")
        assert isinstance(p, DebridProvider)

    def test_resolve_returns_links(self):
        p = FakeProvider(token="abc")
        links = p.resolve("magnet:?xt=urn:btih:abc")
        assert len(links) == 1
        assert links[0].url == "http://example.com/file.mkv"

    def test_unrestrict_returns_link(self):
        p = FakeProvider(token="abc")
        link = p.unrestrict("http://restricted.com")
        assert link.url == "http://restricted.com"
