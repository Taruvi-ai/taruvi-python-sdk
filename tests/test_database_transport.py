"""Database response contracts through the public clients and real HTTPX stack."""

import inspect
import json

import httpx
import pytest

from taruvi import Client


async def resolve(value):
    return await value if inspect.isawaitable(value) else value


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize("wire_shape", ["records", "legacy-list"])
async def test_bulk_update_returns_rows_and_preserves_the_patch_request(mode, wire_shape):
    payload = [{"id": 31, "name": "updated"}, {"id": 32, "description": "persisted"}]
    rows = [{"id": 31, "name": "updated"}, {"id": 32, "description": "persisted", "name": "kept"}]
    requests = []

    def handle(request):
        requests.append(request)
        data = {"records": rows, "count": 2} if wire_shape == "records" else rows
        return httpx.Response(200, json={"status": "success", "data": data})

    client = Client(
        api_url="https://fixture.invalid/sites/sdk-live",
        app_slug="fixture-app",
        mode=mode,
        api_key="owned-fixture-key",
        max_retries=0,
        _env_file=None,
    )
    await resolve(client.close())
    transport_class = httpx.AsyncClient if mode == "async" else httpx.Client
    client._http_client.client = transport_class(
        base_url=client.config.api_url, transport=httpx.MockTransport(handle), trust_env=False
    )
    try:
        result = await resolve(client.database.update("records", payload))
    finally:
        await resolve(client.close())

    assert result == rows
    assert len(requests) == 1
    assert requests[0].method == "PATCH"
    assert requests[0].url.path == "/sites/sdk-live/api/apps/fixture-app/datatables/records/data/"
    assert json.loads(requests[0].content) == payload
