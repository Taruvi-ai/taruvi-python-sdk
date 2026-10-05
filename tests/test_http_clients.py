"""Focused transport contract tests for the sync and async HTTP clients.

These tests use httpx.MockTransport to exercise the SDK boundary without
pretending that an API response came from a module-specific mock.  Integration
tests remain responsible for validating the platform contract itself.
"""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from taruvi._async.http_client import AsyncHTTPClient
from taruvi._sync.http_client import HTTPClient
from taruvi.config import TaruviConfig
from taruvi.exceptions import (
    AuthenticationError,
    NotAuthenticatedError,
    ResponseError,
    ServiceUnavailableError,
    TimeoutError,
)


def _config(**kwargs) -> TaruviConfig:
    return TaruviConfig(
        api_url="https://api.example.com",
        app_slug="test-app",
        max_retries=2,
        **kwargs,
    )


def _sync_client(handler, **config_kwargs) -> HTTPClient:
    client = HTTPClient(_config(**config_kwargs))
    client.client.close()
    client.client = httpx.Client(
        base_url="https://api.example.com",
        transport=httpx.MockTransport(handler),
    )
    return client


async def _async_client(handler, **config_kwargs) -> AsyncHTTPClient:
    client = AsyncHTTPClient(_config(**config_kwargs))
    # Replace the network transport while keeping the SDK's real request loop.
    # The initial client is closed so the fixture never leaks a connection pool.
    await client.close()
    client.client = httpx.AsyncClient(
        base_url="https://api.example.com",
        transport=httpx.MockTransport(handler),
    )
    return client


def test_sync_client_sends_merged_headers_and_decodes_json():
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        seen["headers"] = dict(request.headers)
        return httpx.Response(200, json={"status": "success", "data": {"id": 1}})

    client = _sync_client(handler, api_key="secret", execution_id="exec-1")
    try:
        assert client.get("/api/apps/test-app", headers={"X-Test": "yes"}) == {
            "status": "success",
            "data": {"id": 1},
        }
    finally:
        client.close()

    assert seen["url"] == "https://api.example.com/api/apps/test-app"
    assert seen["headers"]["authorization"] == "Api-Key secret"
    assert seen["headers"]["x-execution-id"] == "exec-1"
    assert seen["headers"]["x-test"] == "yes"


def test_sync_client_handles_empty_and_invalid_json_responses():
    empty = _sync_client(lambda request: httpx.Response(204))
    try:
        assert empty.get("/api/empty") == {}
    finally:
        empty.close()

    invalid = _sync_client(lambda request: httpx.Response(200, content=b"not-json"))
    try:
        with pytest.raises(ResponseError, match="Failed to parse JSON"):
            invalid.get("/api/invalid")
    finally:
        invalid.close()


def test_unauthenticated_and_authenticated_401_responses_are_distinct():
    handler = lambda request: httpx.Response(401, json={"message": "expired"})
    unauthenticated = _sync_client(handler)
    try:
        with pytest.raises(NotAuthenticatedError):
            unauthenticated.get("/api/private")
    finally:
        unauthenticated.close()

    authenticated = _sync_client(handler, api_key="key")
    try:
        with pytest.raises(AuthenticationError) as exc_info:
            authenticated.get("/api/private")
    finally:
        authenticated.close()
    assert not isinstance(exc_info.value, NotAuthenticatedError)


@patch("taruvi._sync.http_client.time.sleep")
def test_sync_retries_only_a_safe_request_after_read_timeout(sleep):
    calls = {"count": 0}

    def handler(request):
        calls["count"] += 1
        if calls["count"] == 1:
            raise httpx.ReadTimeout("temporary read failure")
        return httpx.Response(200, json={"ok": True})

    client = _sync_client(handler)
    try:
        assert client.get("/api/retry") == {"ok": True}
    finally:
        client.close()
    assert calls["count"] == 2
    sleep.assert_called_once_with(1)


@patch("taruvi._sync.http_client.time.sleep")
def test_sync_does_not_retry_post_after_read_timeout(sleep):
    calls = {"count": 0}

    def handler(request):
        calls["count"] += 1
        raise httpx.ReadTimeout("request may have reached server")

    client = _sync_client(handler)
    try:
        with pytest.raises(TimeoutError):
            client.post("/api/mutate", json={"value": 1})
    finally:
        client.close()
    assert calls["count"] == 1
    sleep.assert_not_called()


@pytest.mark.asyncio
async def test_async_client_matches_sync_response_and_error_contracts():
    client = await _async_client(lambda request: httpx.Response(200, json={"ok": True}))
    try:
        assert await client.get("/api/ok") == {"ok": True}
    finally:
        await client.close()

    client = await _async_client(lambda request: httpx.Response(503, json={"message": "down"}))
    try:
        with pytest.raises(ServiceUnavailableError) as exc_info:
            await client.get("/api/down")
    finally:
        await client.close()
    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_async_get_retries_and_async_post_is_not_retried_after_read_timeout():
    calls = {"count": 0}

    def get_handler(request):
        calls["count"] += 1
        if calls["count"] == 1:
            raise httpx.ReadTimeout("temporary")
        return httpx.Response(200, json={"ok": True})

    client = await _async_client(get_handler)
    try:
        with patch("taruvi._async.http_client.asyncio.sleep", new_callable=AsyncMock) as sleep:
            assert await client.get("/api/retry") == {"ok": True}
            sleep.assert_awaited_once_with(1)
    finally:
        await client.close()

    calls["count"] = 0

    def post_handler(request):
        calls["count"] += 1
        raise httpx.ReadTimeout("request may have reached server")

    client = await _async_client(post_handler)
    try:
        with patch("taruvi._async.http_client.asyncio.sleep", new_callable=AsyncMock) as sleep:
            with pytest.raises(TimeoutError):
                await client.post("/api/mutate", json={"value": 1})
            sleep.assert_not_awaited()
    finally:
        await client.close()
    assert calls["count"] == 1
