"""Retries must never resend a request the server may already have applied."""

from unittest import mock

import httpx
import pytest

from taruvi._sync.http_client import HTTPClient
from taruvi.config import TaruviConfig
from taruvi.exceptions import ConnectionError, TimeoutError


def _client(handler) -> HTTPClient:
    config = TaruviConfig(
        api_url="https://api.example.com", app_slug="test-app", api_key="key", max_retries=3
    )
    http = HTTPClient(config)
    http.client.close()
    http.client = httpx.Client(
        base_url="https://api.example.com", transport=httpx.MockTransport(handler)
    )
    return http


def _counting(error: Exception):
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        raise error

    return calls, handler


@mock.patch("time.sleep")
def test_post_is_not_resent_after_a_read_timeout(_sleep):
    calls, handler = _counting(httpx.ReadTimeout("slow"))
    with pytest.raises(TimeoutError):
        _client(handler).post("/api/apps/test-app/functions/f/execute/", json={})
    assert calls["count"] == 1


@mock.patch("time.sleep")
def test_get_is_retried_after_a_read_timeout(_sleep):
    calls, handler = _counting(httpx.ReadTimeout("slow"))
    with pytest.raises(TimeoutError):
        _client(handler).get("/api/apps/test-app/datatables/t/data/")
    assert calls["count"] == 4


@mock.patch("time.sleep")
def test_post_is_retried_when_the_connection_never_opened(_sleep):
    calls, handler = _counting(httpx.ConnectError("refused"))
    with pytest.raises(ConnectionError):
        _client(handler).post("/api/apps/test-app/datatables/t/data/", json={})
    assert calls["count"] == 4


def test_post_passes_a_per_request_timeout():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["timeout"] = request.extensions.get("timeout")
        return httpx.Response(200, json={"status": "success", "data": None})

    _client(handler).post("/api/apps/test-app/functions/f/execute/", json={}, timeout=300)
    assert seen["timeout"]["read"] == 300


def _sdk_client(handler):
    from taruvi import Client

    client = Client(
        api_url="https://api.example.com", app_slug="test-app", api_key="key", mode="sync"
    )
    client._http_client.client.close()
    client._http_client.client = httpx.Client(
        base_url="https://api.example.com", transport=httpx.MockTransport(handler)
    )
    return client


def test_upload_sends_a_guessed_content_type():
    import io

    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = request.read()
        return httpx.Response(
            200,
            json={
                "status": "success",
                "data": {"uploaded_count": 1, "failed_count": 0, "successful": [], "failed": []},
            },
        )

    result = (
        _sdk_client(handler)
        .storage.from_("docs")
        .upload(files=[("chart.png", io.BytesIO(b"png"))], paths=["charts/chart.png"])
    )
    assert b"Content-Type: image/png" in seen["body"]
    assert result["uploaded_count"] == 1


def test_upload_failure_raises_an_sdk_error():
    import io

    from taruvi import AuthorizationError

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"status": "error", "code": "FORBIDDEN", "message": "No"})

    with pytest.raises(AuthorizationError):
        _sdk_client(handler).storage.from_("docs").upload(
            files=[("a.txt", io.BytesIO(b"a"))], paths=["a.txt"]
        )


def test_download_raises_on_error_and_encodes_the_path():
    from taruvi import NotFoundError

    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.raw_path.decode()
        return httpx.Response(
            404, json={"status": "error", "code": "NOT_FOUND", "message": "Missing"}
        )

    with pytest.raises(NotFoundError):
        _sdk_client(handler).storage.from_("docs").download("reports/Q3 #1?.pdf")
    assert seen["path"].endswith("/objects/reports/Q3%20%231%3F.pdf/")


def test_storage_delete_returns_skipped_objects():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            207,
            json={
                "status": "success",
                "data": {
                    "deleted_count": 0,
                    "failed": [{"path": "a.txt", "error": "Permission denied"}],
                },
            },
        )

    result = _sdk_client(handler).storage.from_("docs").delete(["a.txt"])
    assert result["failed"] == [{"path": "a.txt", "error": "Permission denied"}]
