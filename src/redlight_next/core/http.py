from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

import requests

from redlight_next.core.errors import HTTPClientError

DEFAULT_USER_AGENT = "RedLightNext/0.1"


@dataclass(frozen=True)
class HTTPResponse:
    status_code: int
    text: str
    content: bytes
    headers: Mapping[str, str]

    def json(self) -> Any:
        try:
            return json.loads(self.text)
        except ValueError as exc:
            raise HTTPClientError("Response did not contain valid JSON") from exc


@dataclass
class HTTPClient:
    timeout: float = 15.0
    retries: int = 2
    backoff_seconds: float = 0.25
    user_agent: str = DEFAULT_USER_AGENT
    session: Any = field(default_factory=requests.Session)

    def request(self, method: str, url: str, **kwargs: Any) -> HTTPResponse:
        headers = dict(kwargs.pop("headers", {}) or {})
        headers.setdefault("User-Agent", self.user_agent)
        timeout = kwargs.pop("timeout", self.timeout)
        last_error: Optional[Exception] = None
        for attempt in range(self.retries + 1):
            try:
                response = self.session.request(method, url, headers=headers, timeout=timeout, **kwargs)
                if response.status_code == 429:
                    raise HTTPClientError("Rate limited by remote API")
                if response.status_code >= 400:
                    raise HTTPClientError(f"HTTP {response.status_code} for {method.upper()} {url}")
                return HTTPResponse(response.status_code, response.text, response.content, dict(response.headers))
            except (requests.RequestException, HTTPClientError) as exc:
                last_error = exc
                if attempt >= self.retries:
                    break
                time.sleep(self.backoff_seconds * (attempt + 1))
        raise HTTPClientError(str(last_error)) from last_error

    def get(self, url: str, **kwargs: Any) -> HTTPResponse:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> HTTPResponse:
        return self.request("POST", url, **kwargs)
