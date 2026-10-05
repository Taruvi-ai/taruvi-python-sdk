"""Saved internal SQL executes bound parameters and stays in its URL app."""

from uuid import UUID

import pytest

from taruvi.exceptions import NotFoundError, ValidationError

pytestmark = pytest.mark.integration


def assert_result(result, value):
    assert result["status"] == "success"
    assert result["data"] == [{"value": value}]
    assert result["total"] == 1
    UUID(result["execution_key"])


async def test_async_bound_query_returns_exact_values(async_analytics_module, live_resources):
    query = live_resources["analytics"]["query_slug"]
    keys = set()
    for value in ("'; DROP TABLE analytics_analyticsquery; --", ""):
        result = await async_analytics_module.execute(query, params={"value": value})
        assert_result(result, value)
        keys.add(result["execution_key"])
    assert len(keys) == 2


def test_sync_bound_query_returns_exact_values(sync_analytics_module, live_resources):
    query = live_resources["analytics"]["query_slug"]
    keys = set()
    for value in ("'; DROP TABLE analytics_analyticsquery; --", ""):
        result = sync_analytics_module.execute(query, params={"value": value})
        assert_result(result, value)
        keys.add(result["execution_key"])
    assert len(keys) == 2


async def test_async_query_refuses_missing_params_and_wrong_app(
    async_analytics_module, live_resources, live_manifest
):
    api = async_analytics_module
    query = live_resources["analytics"]["query_slug"]
    with pytest.raises(ValidationError) as invalid:
        await api.execute(query)
    assert invalid.value.status_code == 400
    with pytest.raises(NotFoundError) as wrong_app:
        await api.execute(
            query, params={"value": "hidden"}, app_slug=live_resources["other_app_slug"]
        )
    assert wrong_app.value.status_code == 404
    with pytest.raises(NotFoundError) as missing:
        await api.execute(f"{live_manifest['fixture_id']}-missing", params={"value": "missing"})
    assert missing.value.status_code == 404


def test_sync_query_refuses_missing_params_and_wrong_app(
    sync_analytics_module, live_resources, live_manifest
):
    api = sync_analytics_module
    query = live_resources["analytics"]["query_slug"]
    with pytest.raises(ValidationError) as invalid:
        api.execute(query)
    assert invalid.value.status_code == 400
    with pytest.raises(NotFoundError) as wrong_app:
        api.execute(query, params={"value": "hidden"}, app_slug=live_resources["other_app_slug"])
    assert wrong_app.value.status_code == 404
    with pytest.raises(NotFoundError) as missing:
        api.execute(f"{live_manifest['fixture_id']}-missing", params={"value": "missing"})
    assert missing.value.status_code == 404
