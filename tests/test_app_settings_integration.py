"""App settings: exact owned defaults, alternate app scope, and typed refusals."""

import pytest

from taruvi.exceptions import ConfigurationError, NotAuthenticatedError, NotFoundError

_FIELDS = {
    "display_name",
    "primary_color",
    "secondary_color",
    "icon",
    "icon_url",
    "icon_background_color",
    "category",
    "documentation_url",
    "support_email",
    "default_frontend_worker_url",
    "default_frontend_worker_slug",
    "created_at",
    "updated_at",
}


def assert_settings(response, expected):
    assert response["status"] == "success"
    data = response["data"]
    assert set(data) == _FIELDS
    assert {key: data[key] for key in expected} == expected


@pytest.mark.integration
async def test_async_settings_uses_requested_app(async_app_module, live_resources):
    assert_settings(await async_app_module.settings(), live_resources["app_settings"])
    assert_settings(
        await async_app_module.settings(app_slug=live_resources["other_app_slug"]),
        live_resources["other_app_settings"],
    )


@pytest.mark.integration
def test_sync_settings_uses_requested_app(sync_app_module, live_resources):
    assert_settings(sync_app_module.settings(), live_resources["app_settings"])
    assert_settings(
        sync_app_module.settings(app_slug=live_resources["other_app_slug"]),
        live_resources["other_app_settings"],
    )


@pytest.mark.integration
async def test_async_settings_refuses_missing_app_and_anonymous(
    async_app_module, anonymous_async_client, live_manifest
):
    with pytest.raises(NotFoundError) as missing:
        await async_app_module.settings(app_slug=f"{live_manifest['fixture_id']}-missing")
    assert missing.value.status_code == 404
    with pytest.raises(NotAuthenticatedError) as anonymous:
        await anonymous_async_client.app.settings()
    assert anonymous.value.status_code == 401


@pytest.mark.integration
def test_sync_settings_refuses_missing_app_and_anonymous(
    sync_app_module, anonymous_sync_client, live_manifest
):
    with pytest.raises(NotFoundError) as missing:
        sync_app_module.settings(app_slug=f"{live_manifest['fixture_id']}-missing")
    assert missing.value.status_code == 404
    with pytest.raises(NotAuthenticatedError) as anonymous:
        anonymous_sync_client.app.settings()
    assert anonymous.value.status_code == 401


def test_settings_requires_app_slug(monkeypatch):
    monkeypatch.setenv("TARUVI_TEST_MODE", "true")
    from taruvi import Client

    with pytest.raises(ConfigurationError, match="app_slug is required"):
        Client(api_url="https://example.invalid", app_slug="")
