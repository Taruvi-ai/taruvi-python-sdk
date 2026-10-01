"""Credential selection: one explicit credential, one header."""

import httpx
import pytest

from taruvi import Client, ConnectionError
from taruvi.config import TaruviConfig


@pytest.fixture
def env_api_key(monkeypatch):
    monkeypatch.delenv("TARUVI_TEST_MODE", raising=False)
    monkeypatch.setenv("TARUVI_API_KEY", "env-key")


def test_explicit_session_token_ignores_api_key_from_environment(env_api_key):
    client = Client("https://api.example.com", "app", session_token="user-session", mode="sync")
    headers = client.config.headers
    assert headers.get("X-Session-Token") == "user-session"
    assert "Authorization" not in headers


def test_environment_credential_still_used_when_none_is_passed(env_api_key):
    client = Client("https://api.example.com", "app", mode="sync")
    assert client.config.headers["Authorization"] == "Api-Key env-key"


def test_only_one_credential_header_is_sent():
    config = TaruviConfig(api_url="https://api.example.com", app_slug="app", api_key="k", session_token="s")
    assert config.headers["Authorization"] == "Api-Key k"
    assert "X-Session-Token" not in config.headers


def test_trailing_slash_is_removed_from_api_url():
    config = TaruviConfig(api_url="https://api.example.com/", app_slug="app")
    assert config.api_url == "https://api.example.com"


def _client(handler):
    client = Client("https://api.example.com", "app", api_key="k", mode="sync", max_retries=2)
    client._http_client.client.close()
    client._http_client.client = httpx.Client(
        base_url="https://api.example.com", transport=httpx.MockTransport(handler)
    )
    return client


def test_count_requests_a_single_row():
    seen = {}

    def handler(request):
        seen["query"] = dict(request.url.params)
        return httpx.Response(200, json={"status": "success", "data": [], "total": 42})

    assert _client(handler).database.from_("tasks").page(3).count() == 42
    assert seen["query"]["page_size"] == "1"
    assert "page" not in seen["query"]


def test_download_connection_failure_raises_sdk_error():
    def handler(request):
        raise httpx.ConnectError("refused")

    with pytest.raises(ConnectionError):
        _client(handler).storage.from_("docs").download("a.txt")


def test_dropped_connection_on_get_is_retried_and_wrapped(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _: None)
    calls = {"count": 0}

    def handler(request):
        calls["count"] += 1
        raise httpx.RemoteProtocolError("Server disconnected")

    with pytest.raises(ConnectionError):
        _client(handler).database.from_("tasks").execute()
    assert calls["count"] == 3


def test_requests_identify_the_sdk_and_version():
    import taruvi

    seen = {}

    def handler(request):
        seen.update(request.headers)
        return httpx.Response(200, json={"status": "success", "data": [], "total": 0})

    _client(handler).database.from_("tasks").page_size(1).execute()
    expected_prefix = f"taruvi-python/{taruvi.__version__} (python/"
    assert seen["x-taruvi-client"].startswith(expected_prefix)
    assert seen["user-agent"] == seen["x-taruvi-client"]
