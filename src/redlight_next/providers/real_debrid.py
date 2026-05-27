from __future__ import annotations

from typing import Any, Dict, List, Optional

from redlight_next.core.http import HTTPClient
from redlight_next.core.errors import ProviderError
from redlight_next.providers.base import (
    BaseDebridProvider,
    ProviderHealth,
    ProviderStatus,
    ResolvedLink,
)


class RealDebridProvider(BaseDebridProvider):
    """Real-Debrid API client."""

    BASE_URL = "https://api.real-debrid.com/rest/1.0"

    def __init__(self, token: str, enabled: bool = True, timeout: int = 30, client: Optional[Any] = None):
        super().__init__(token, enabled, timeout)
        self._client = client or HTTPClient(timeout=timeout)

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self.BASE_URL}{path}"
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self._token}"
        response = self._client.request(method, url, headers=headers, **kwargs)
        if response.status_code == 401:
            raise ProviderError("Real-Debrid authentication failed")
        if response.status_code == 429:
            raise ProviderError("Real-Debrid rate limited")
        if response.status_code >= 400:
            raise ProviderError(f"Real-Debrid error {response.status_code}")
        return response.json()

    def health(self) -> ProviderHealth:
        if not self._enabled:
            return ProviderHealth(status=ProviderStatus.DISABLED)
        try:
            data = self._request("GET", "/user")
            return ProviderHealth(
                status=ProviderStatus.OK,
                quota_info={"premium": data.get("premium", 0), "username": data.get("username", "")},
            )
        except Exception as exc:
            if "authentication" in str(exc).lower():
                return ProviderHealth(status=ProviderStatus.AUTH_ERROR, message=str(exc))
            return ProviderHealth(status=ProviderStatus.UNAVAILABLE, message=str(exc))

    def resolve(self, magnet_or_url: str) -> List[ResolvedLink]:
        if not self._enabled:
            return []
        try:
            if magnet_or_url.startswith("magnet:?"):
                data = self._request("POST", "/torrents/addMagnet", data={"magnet": magnet_or_url})
                torrent_id = data.get("id")
                if not torrent_id:
                    return []
                info = self._request("GET", f"/torrents/info/{torrent_id}")
                links = info.get("links", [])
            else:
                data = self._request("POST", "/unrestrict/link", data={"link": magnet_or_url})
                links = [data.get("download", "")]

            result = []
            for link in links:
                if not link:
                    continue
                unrestricted = self._request("POST", "/unrestrict/link", data={"link": link})
                result.append(
                    ResolvedLink(
                        url=unrestricted.get("download", ""),
                        quality="unknown",
                        filename=unrestricted.get("filename"),
                        size_bytes=unrestricted.get("filesize"),
                    )
                )
            return result
        except Exception as exc:
            raise ProviderError(f"Real-Debrid resolve failed: {exc}") from exc

    def unrestrict(self, url: str) -> ResolvedLink:
        if not self._enabled:
            raise ProviderError("Real-Debrid is disabled")
        try:
            data = self._request("POST", "/unrestrict/link", data={"link": url})
            return ResolvedLink(
                url=data.get("download", ""),
                filename=data.get("filename"),
                size_bytes=data.get("filesize"),
            )
        except Exception as exc:
            raise ProviderError(f"Real-Debrid unrestrict failed: {exc}") from exc
