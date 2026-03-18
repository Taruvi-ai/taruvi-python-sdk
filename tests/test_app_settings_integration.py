"""
Integration tests for App Settings API.

IMPORTANT: These are REAL integration tests - NO MOCKS!
- Makes actual HTTP requests to Taruvi backend
- Tests app settings retrieval via GET /api/apps/{app_slug}/settings/

Setup:
    1. Ensure .env is configured with backend URL and credentials
    2. Backend must have an app with settings configured
    3. Run: RUN_INTEGRATION_TESTS=1 pytest tests/test_app_settings_integration.py -v
"""

import pytest


# ============================================================================
# App Settings Tests - Async
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_app_settings_async(async_app_module):
    """Test retrieving app settings (async)."""
    try:
        result = await async_app_module.settings()

        assert result is not None
        assert isinstance(result, dict)
        # Verify expected fields from AppSettingSerializer
        expected_fields = [
            "display_name", "primary_color", "secondary_color",
            "icon", "icon_url", "icon_background_color", "category",
            "documentation_url", "support_email",
            "default_frontend_worker_url", "created_at", "updated_at",
        ]
        data = result.get("data", result)
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"

    except Exception as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            pytest.skip(f"Skipping: App settings not configured - {e}")
        raise


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_app_settings_with_slug_override_async(async_app_module):
    """Test retrieving app settings with explicit app_slug (async)."""
    try:
        result = await async_app_module.settings(app_slug="test-app")

        assert result is not None
        assert isinstance(result, dict)

    except Exception as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            pytest.skip(f"Skipping: App 'test-app' not found - {e}")
        raise


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_app_settings_nonexistent_app_async(async_app_module):
    """Test retrieving settings for non-existent app raises error (async)."""
    from taruvi.exceptions import NotFoundError, APIError

    try:
        await async_app_module.settings(app_slug="nonexistent-app-99999")
        pytest.fail("Expected error for non-existent app")
    except (NotFoundError, APIError):
        pass  # Expected


# ============================================================================
# App Settings Tests - Sync
# ============================================================================

@pytest.mark.integration
def test_get_app_settings_sync(sync_app_module):
    """Test retrieving app settings (sync)."""
    try:
        result = sync_app_module.settings()

        assert result is not None
        assert isinstance(result, dict)
        expected_fields = [
            "display_name", "primary_color", "secondary_color",
            "icon", "icon_url", "icon_background_color", "category",
            "documentation_url", "support_email",
            "default_frontend_worker_url", "created_at", "updated_at",
        ]
        data = result.get("data", result)
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"

    except Exception as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            pytest.skip(f"Skipping: App settings not configured - {e}")
        raise


@pytest.mark.integration
def test_get_app_settings_with_slug_override_sync(sync_app_module):
    """Test retrieving app settings with explicit app_slug (sync)."""
    try:
        result = sync_app_module.settings(app_slug="test-app")

        assert result is not None
        assert isinstance(result, dict)

    except Exception as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            pytest.skip(f"Skipping: App 'test-app' not found - {e}")
        raise


@pytest.mark.integration
def test_get_app_settings_nonexistent_app_sync(sync_app_module):
    """Test retrieving settings for non-existent app raises error (sync)."""
    from taruvi.exceptions import NotFoundError, APIError

    try:
        sync_app_module.settings(app_slug="nonexistent-app-99999")
        pytest.fail("Expected error for non-existent app")
    except (NotFoundError, APIError):
        pass  # Expected


# ============================================================================
# Validation Tests (no backend needed)
# ============================================================================

def test_settings_requires_app_slug(monkeypatch):
    """Test that settings() raises ValueError when no app_slug is available."""
    monkeypatch.setenv("TARUVI_TEST_MODE", "true")

    from taruvi import Client

    client = Client(api_url="http://localhost:8000", app_slug="")

    with pytest.raises(ValueError, match="app_slug is required"):
        client.app.settings()
