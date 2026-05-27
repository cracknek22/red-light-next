import pytest

from redlight_next.core.errors import HTTPClientError
from redlight_next.core.http import HTTPClient, HTTPResponse


class FakeResponse:
    def __init__(self, status_code=200, text='{"ok": true}', headers=None):
        self.status_code = status_code
        self.text = text
        self.content = text.encode("utf-8")
        self.headers = headers or {"x-test": "1"}


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def test_http_client_sets_timeout_and_user_agent():
    session = FakeSession([FakeResponse()])
    client = HTTPClient(session=session, timeout=3, retries=0, user_agent="TestUA")

    response = client.get("https://example.test")

    assert response.json() == {"ok": True}
    assert session.calls[0][2]["timeout"] == 3
    assert session.calls[0][2]["headers"]["User-Agent"] == "TestUA"


def test_http_client_raises_on_http_error():
    client = HTTPClient(session=FakeSession([FakeResponse(status_code=500, text="no")]), retries=0)

    with pytest.raises(HTTPClientError):
        client.get("https://example.test")


def test_http_response_json_error_is_wrapped():
    response = HTTPResponse(status_code=200, text="not-json", content=b"not-json", headers={})

    with pytest.raises(HTTPClientError):
        response.json()
