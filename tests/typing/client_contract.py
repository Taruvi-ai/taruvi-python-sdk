"""Consumer declarations through the public Client factory; never execute this file."""

from typing import Any, Union

import httpx
from typing_extensions import assert_type

from taruvi import Client, FunctionExecutionResponse, TaruviConfig, UserResponse
from taruvi._async.client import AsyncClient
from taruvi._sync.client import SyncClient

API_URL = "https://example.invalid"
APP = "typing-probe"


def sync_contract() -> None:
    client = Client(API_URL, APP, mode="sync")
    assert_type(client, SyncClient)
    assert_type(client.config, TaruviConfig)
    assert_type(client._http_client.client, httpx.Client)
    assert_type(client.functions.execute("sample"), FunctionExecutionResponse)
    assert_type(client.functions.execute("sample", is_async=True), FunctionExecutionResponse)
    assert_type(client.database.from_("items").execute(), dict[str, Any])
    assert_type(client.storage.from_("documents").list(), dict[str, Any])
    file = client.storage.from_("documents").update("report.txt", metadata={"reviewed": True})
    assert_type(file["id"], int)
    assert_type(file["uuid"], str)
    assert_type(file["file_path"], str)
    assert_type(file["file_url"], Union[str, None])
    assert_type(client.secrets.list(), dict[str, Any])
    assert_type(client.policy.filter_allowed([], ["read"]), list[dict[str, Any]])
    policy = client.policy.check_resources([])
    assert_type(policy.get("request_id"), Union[str, None])
    assert_type(policy.get("cerbos_call_id"), Union[str, None])
    assert_type(policy["results"][0].get("validation_errors"), Union[list[dict[str, Any]], None])
    assert_type(client.app.roles(), dict[str, Any])
    assert_type(client.settings.get(), dict[str, Any])
    assert_type(client.users.list(), dict[str, Any])
    assert_type(client.users.get("alice"), UserResponse)
    assert_type(client.analytics.execute("sample"), dict[str, Any])
    assert_type(client.auth.signInWithToken("token"), SyncClient)
    assert_type(client.auth.signInWithPassword("email", "password"), SyncClient)
    assert_type(client.auth.signOut(), SyncClient)
    assert_type(client.close(), None)
    with Client(API_URL, APP, mode="sync") as entered:
        assert_type(entered, SyncClient)


async def async_contract() -> None:
    client = Client(API_URL, APP, mode="async")
    assert_type(client, AsyncClient)
    assert_type(client.config, TaruviConfig)
    assert_type(client._http_client.client, httpx.AsyncClient)
    assert_type(await client.functions.execute("sample"), FunctionExecutionResponse)
    assert_type(await client.functions.execute("sample", is_async=False), FunctionExecutionResponse)
    assert_type(await client.database.from_("items").execute(), dict[str, Any])
    assert_type(await client.storage.from_("documents").list(), dict[str, Any])
    file = await client.storage.from_("documents").update("report.txt", metadata={"reviewed": True})
    assert_type(file["id"], int)
    assert_type(file["uuid"], str)
    assert_type(file["file_path"], str)
    assert_type(file["file_url"], Union[str, None])
    assert_type(await client.secrets.list(), dict[str, Any])
    assert_type(await client.policy.filter_allowed([], ["read"]), list[dict[str, Any]])
    policy = await client.policy.check_resources([])
    assert_type(policy.get("request_id"), Union[str, None])
    assert_type(policy.get("cerbos_call_id"), Union[str, None])
    assert_type(policy["results"][0].get("validation_errors"), Union[list[dict[str, Any]], None])
    assert_type(await client.app.roles(), dict[str, Any])
    assert_type(await client.settings.get(), dict[str, Any])
    assert_type(await client.users.list(), dict[str, Any])
    assert_type(await client.users.get("alice"), UserResponse)
    assert_type(await client.analytics.execute("sample"), dict[str, Any])
    assert_type(client.auth.signInWithToken("token"), AsyncClient)
    assert_type(await client.auth.signInWithPassword("email", "password"), AsyncClient)
    assert_type(client.auth.signOut(), AsyncClient)
    assert_type(await client.close(), None)
    async with Client(API_URL, APP, mode="async") as entered:
        assert_type(entered, AsyncClient)


def autodetected_contract(mode: str | None) -> None:
    assert_type(Client(API_URL, APP), Union[AsyncClient, SyncClient])
    assert_type(Client(API_URL, APP, mode=None), Union[AsyncClient, SyncClient])
    assert_type(Client(API_URL, APP, mode=mode), Union[AsyncClient, SyncClient])
