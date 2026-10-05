"""High-value request contracts for modules whose live tests need a backend.

The assertions focus on URL, query, and payload boundaries.  They complement
the opt-in integration suite without duplicating every CRUD response shape.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from taruvi._async.modules.functions import AsyncFunctionsModule
from taruvi._sync.modules.analytics import AnalyticsModule
from taruvi._sync.modules.app import AppModule
from taruvi._sync.modules.functions import FunctionsModule
from taruvi._sync.modules.policy import PolicyModule
from taruvi._sync.modules.secrets import SecretsModule
from taruvi._sync.modules.settings import SettingsModule
from taruvi._sync.modules.storage import StorageQueryBuilder
from taruvi._sync.modules.users import UsersModule


def _client(http=None, app_slug="demo"):
    return SimpleNamespace(
        _config=SimpleNamespace(app_slug=app_slug, api_url="https://api.example.com"),
        _http_client=http or MagicMock(),
    )


def test_analytics_app_and_site_settings_use_expected_routes():
    http = MagicMock()
    http.get.return_value = {"data": {}}
    http.post.return_value = {"data": []}
    client = _client(http)

    AnalyticsModule(client).execute("revenue", {"month": "2026-10"})
    AppModule(client).roles()
    AppModule(client).settings(app_slug="other")
    SettingsModule(client).get()

    http.post.assert_called_once_with(
        "/api/apps/demo/analytics/queries/revenue/execute/",
        json={"params": {"month": "2026-10"}},
    )
    assert [call.args[0] for call in http.get.call_args_list] == [
        "/api/apps/demo/roles/",
        "/api/apps/other/settings/",
        "/api/settings/metadata/",
    ]


def test_functions_send_explicit_async_flag_and_pagination():
    http = MagicMock()
    http.post.return_value = {"invocation": {}}
    http.get.return_value = {"data": []}
    functions = FunctionsModule(_client(http))

    functions.execute("rebuild", {"dry_run": True}, is_async=False, timeout=5)
    functions.list(limit=10, offset=20)

    http.post.assert_called_once_with(
        "/api/apps/demo/functions/rebuild/execute/",
        json={"params": {"dry_run": True}, "async": False},
        headers={},
        timeout=5,
    )
    http.get.assert_called_once_with(
        "/api/apps/demo/functions/", params={"limit": 10, "offset": 20}
    )


def test_policy_filters_only_resources_with_every_requested_action():
    http = MagicMock()
    http.post.return_value = {
        "results": [
            {"actions": {"read": "EFFECT_ALLOW", "write": "EFFECT_ALLOW"}},
            {"actions": {"read": "EFFECT_ALLOW", "write": "EFFECT_DENY"}},
        ]
    }
    resources = [{"kind": "datatable", "id": "a"}, {"kind": "datatable", "id": "b"}]

    allowed = PolicyModule(_client(http)).filter_allowed(resources, ["read", "write"])

    assert allowed == [resources[0]]
    http.post.assert_called_once_with(
        "/api/apps/demo/check/resources/",
        json={
            "resources": [{"resource": item, "actions": ["read", "write"]} for item in resources]
        },
    )


def test_secrets_and_users_preserve_filters_and_mutation_routes():
    http = MagicMock()
    http.get.return_value = {"data": {}}
    http.post.return_value = {"data": {}}
    http.put.return_value = {"data": {}}
    http.delete.return_value = {"data": {}}
    client = _client(http)

    secrets = SecretsModule(client)
    secrets.list(keys=["A", "B"], tags=["prod"], page=2)
    secrets.get("A", tags=["prod", "critical"])
    users = UsersModule(client)
    users.create({"username": "alice"})
    users.update("alice", {"is_active": False})
    users.delete("alice")
    users.list(search="ali", page=2)

    assert http.get.call_args_list[0].args == ("/api/secrets/",)
    assert http.get.call_args_list[0].kwargs["params"] == {
        "keys": "A,B",
        "app": "demo",
        "tags": "prod",
        "include_metadata": False,
        "page": 2,
    }
    assert http.get.call_args_list[1].kwargs["params"] == {
        "app": "demo",
        "tags": "prod,critical",
    }
    assert http.post.call_args == (("/api/users/",), {"json": {"username": "alice"}})
    assert http.put.call_args == (("/api/users/alice/",), {"json": {"is_active": False}})
    assert http.delete.call_args == (("/api/users/alice/",), {})
    assert http.get.call_args_list[2].args[0].startswith("/api/users/?")
    assert "search=ali" in http.get.call_args_list[2].args[0]


def test_storage_builder_encodes_object_paths_and_filters():
    http = MagicMock()
    http.get.return_value = {"data": []}
    client = _client(http)
    bucket = StorageQueryBuilder(client, "documents").filter(search="Q3 report", page_size=5)

    bucket.list()
    bucket.view_access("reports/Q3 #1?.pdf")

    assert http.get.call_args_list[0].args[0] == (
        "/api/apps/demo/storage/buckets/documents/objects/?page_size=5&search=Q3+report"
    )
    assert http.get.call_args_list[1].args[0].endswith("/objects/reports/Q3%20%231%3F.pdf/view/")


@pytest.mark.asyncio
async def test_async_functions_keep_the_same_request_contract():
    http = MagicMock()
    http.post = AsyncMock(return_value={"invocation": {}})
    module = AsyncFunctionsModule(_client(http))

    await module.execute("rebuild", {"dry_run": True}, is_async=True)

    http.post.assert_awaited_once_with(
        "/api/apps/demo/functions/rebuild/execute/",
        json={"params": {"dry_run": True}, "async": True},
        headers={},
        timeout=None,
    )
