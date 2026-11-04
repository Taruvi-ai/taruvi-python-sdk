"""Unauthenticated 401 responses keep Taruvi's UNAUTHORIZED error code."""

import httpx
import pytest

from taruvi import Client
from taruvi.config import TaruviConfig
from taruvi.exceptions import AuthenticationError, NotAuthenticatedError
from taruvi.http_client_base import BaseHTTPClient

UNAUTHORIZED_BODY = {
    "status": "error",
    "message": "Authentication credentials were not provided.",
    "code": "UNAUTHORIZED",
}


def _unauthorized_response(_request: httpx.Request) -> httpx.Response:
    return httpx.Response(401, json=UNAUTHORIZED_BODY)


def _assert_unauthorized(error: AuthenticationError) -> None:
    assert isinstance(error, NotAuthenticatedError)
    assert error.status_code == 401
    assert error.code == "UNAUTHORIZED"


def test_handle_error_response_keeps_unauthorized_code(unauth_test_config):
    config = TaruviConfig(
        api_url=unauth_test_config["api_url"],
        app_slug=unauth_test_config["app_slug"],
    )
    client = BaseHTTPClient(config)
    assert not client._is_client_authenticated()

    with pytest.raises(AuthenticationError) as exc_info:
        client._handle_error_response(httpx.Response(401, json=UNAUTHORIZED_BODY))

    _assert_unauthorized(exc_info.value)


def test_sync_get_current_user_keeps_unauthorized_code(unauth_test_config):
    client = Client(
        api_url=unauth_test_config["api_url"],
        app_slug=unauth_test_config["app_slug"],
        mode="sync",
    )
    client._http_client.client.close()
    client._http_client.client = httpx.Client(
        base_url=unauth_test_config["api_url"],
        transport=httpx.MockTransport(_unauthorized_response),
    )
    try:
        with pytest.raises(AuthenticationError) as exc_info:
            client.auth.get_current_user()
        _assert_unauthorized(exc_info.value)
    finally:
        client._http_client.client.close()


@pytest.mark.asyncio
async def test_async_get_current_user_keeps_unauthorized_code(unauth_test_config):
    client = Client(
        api_url=unauth_test_config["api_url"],
        app_slug=unauth_test_config["app_slug"],
        mode="async",
    )
    await client._http_client.client.aclose()
    client._http_client.client = httpx.AsyncClient(
        base_url=unauth_test_config["api_url"],
        transport=httpx.MockTransport(_unauthorized_response),
    )
    try:
        with pytest.raises(AuthenticationError) as exc_info:
            await client.auth.get_current_user()
        _assert_unauthorized(exc_info.value)
    finally:
        await client._http_client.client.aclose()
