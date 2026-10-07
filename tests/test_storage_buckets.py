"""Bucket retrieve, create, and update return the resource body."""

import httpx
import pytest

from taruvi import Client

_BUCKET = {
    "slug": "oct5pubshareattach",
    "storage_provider": "sharepoint",
    "visibility": "public",
}


def _sync_client(handler):
    client = Client(
        api_url="https://api.example.com",
        app_slug="site_user_app",
        api_key="key",
        mode="sync",
    )
    client._http_client.client.close()
    client._http_client.client = httpx.Client(
        base_url="https://api.example.com", transport=httpx.MockTransport(handler)
    )
    return client


def _json_ok(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json=_BUCKET)


def test_get_bucket_returns_the_resource_when_there_is_no_data_wrapper():
    bucket = _sync_client(_json_ok).storage.get_bucket("oct5pubshareattach")
    assert bucket["storage_provider"] == "sharepoint"
    assert bucket["visibility"] == "public"


def test_get_bucket_still_unwraps_a_data_envelope():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "success", "data": _BUCKET})

    bucket = _sync_client(handler).storage.get_bucket("oct5pubshareattach")
    assert bucket["slug"] == "oct5pubshareattach"


def test_create_and_update_bucket_return_the_resource_body():
    storage = _sync_client(_json_ok).storage
    assert storage.create_bucket("Public")["visibility"] == "public"
    assert storage.update_bucket("oct5pubshareattach", visibility="public")["slug"] == "oct5pubshareattach"


@pytest.mark.asyncio
async def test_async_get_bucket_returns_the_resource_body():
    client = Client(
        api_url="https://api.example.com",
        app_slug="site_user_app",
        api_key="key",
        mode="async",
    )
    await client._http_client.client.aclose()
    client._http_client.client = httpx.AsyncClient(
        base_url="https://api.example.com", transport=httpx.MockTransport(_json_ok)
    )
    try:
        bucket = await client.storage.get_bucket("oct5pubshareattach")
    finally:
        await client._http_client.client.aclose()
    assert bucket["storage_provider"] == "sharepoint"
