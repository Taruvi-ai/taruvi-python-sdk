"""Test the unified Client factory function (v0.2.0+)."""

import pytest
from taruvi import Client
from taruvi.client import _AsyncClient
from taruvi.sync_client import _SyncClient


def test_client_defaults_to_sync():
    """Test that Client() without mode defaults to sync."""
    client = Client(
        api_url="https://api.example.com",
        app_slug="test-app"
    )
    assert isinstance(client, _SyncClient)


def test_client_explicit_sync_mode():
    """Test that Client(mode='sync') returns sync client."""
    client = Client(
        api_url="https://api.example.com",
        app_slug="test-app",
        mode='sync'
    )
    assert isinstance(client, _SyncClient)


def test_client_async_mode():
    """Test that Client(mode='async') returns async client."""
    client = Client(
        api_url="https://api.example.com",
        app_slug="test-app",
        mode='async'
    )
    assert isinstance(client, _AsyncClient)


def test_client_invalid_mode():
    """Test that Client with invalid mode raises ValueError."""
    with pytest.raises(ValueError, match="Invalid mode"):
        Client(
            api_url="https://api.example.com",
            app_slug="test-app",
            mode='invalid'
        )


def test_client_missing_app_slug():
    """Test that Client without required app_slug raises TypeError."""
    with pytest.raises(TypeError):
        Client(
            api_url="https://api.example.com"
            # Missing app_slug - should raise TypeError
        )


def test_client_with_optional_params():
    """Test that Client accepts optional configuration parameters."""
    client = Client(
        api_url="https://api.example.com",
        app_slug="test-app",
        mode='sync',
        timeout=60,
        max_retries=5
    )
    assert isinstance(client, _SyncClient)
    assert client._config.timeout == 60
    assert client._config.max_retries == 5


def test_client_callable():
    """Test that Client is callable."""
    assert callable(Client)


def test_client_has_all_modules():
    """Test that both client types have all expected modules."""
    sync_client = Client(
        api_url="https://api.example.com",
        app_slug="test-app",
        mode='sync'
    )

    async_client = Client(
        api_url="https://api.example.com",
        app_slug="test-app",
        mode='async'
    )

    # Check that all modules are accessible (lazy-loaded)
    expected_modules = ['functions', 'database', 'auth', 'storage', 'secrets', 'policy', 'app', 'settings']

    for module_name in expected_modules:
        assert hasattr(sync_client, module_name), f"Sync client missing {module_name}"
        assert hasattr(async_client, module_name), f"Async client missing {module_name}"


def test_syncclient_import_raises_error():
    """Test that importing SyncClient directly raises ImportError (breaking change)."""
    with pytest.raises(ImportError):
        from taruvi import SyncClient  # noqa: F401
