"""Test the unified Client factory function (v0.2.0)."""

import pytest
from taruvi import Client
from taruvi.client import _AsyncClient
from taruvi.sync_client import _SyncClient


def test_client_defaults_to_sync():
    """Test that Client() without mode defaults to sync."""
    client = Client(
        "https://api.example.com",
        "test-key",
        "test-site",
        "test-app"
    )
    assert isinstance(client, _SyncClient)


def test_client_explicit_sync_mode():
    """Test that Client(mode='sync') returns sync client."""
    client = Client(
        "https://api.example.com",
        "test-key",
        "test-site",
        "test-app",
        'sync'
    )
    assert isinstance(client, _SyncClient)


def test_client_async_mode():
    """Test that Client(mode='async') returns async client."""
    client = Client(
        "https://api.example.com",
        "test-key",
        "test-site",
        "test-app",
        'async'
    )
    assert isinstance(client, _AsyncClient)


def test_client_invalid_mode():
    """Test that Client with invalid mode raises ValueError."""
    with pytest.raises(ValueError, match="Invalid mode"):
        Client(
            "https://api.example.com",
            "test-key",
            "test-site",
            "test-app",
            'invalid'
        )


def test_client_missing_app_slug():
    """Test that Client without required app_slug raises TypeError."""
    with pytest.raises(TypeError):
        Client(
            "https://api.example.com",
            "test-key",
            "test-site"
            # Missing app_slug - should raise TypeError
        )


def test_client_sync_mode_with_verify_ssl():
    """Test that sync mode accepts verify_ssl parameter."""
    client = Client(
        "https://api.example.com",
        "test-key",
        "test-site",
        "test-app",
        'sync',
        verify_ssl=False
    )
    assert isinstance(client, _SyncClient)
    assert client._config.verify_ssl is False


def test_client_async_mode_ignores_sync_only_params():
    """Test that async mode ignores sync-only parameters."""
    # Should not raise an error, just ignore these params
    client = Client(
        "https://api.example.com",
        "test-key",
        "test-site",
        "test-app",
        'async',
        verify_ssl=False,  # Sync-only, should be ignored
        pool_connections=5,  # Sync-only, should be ignored
        pool_maxsize=10  # Sync-only, should be ignored
    )
    assert isinstance(client, _AsyncClient)


def test_client_callable():
    """Test that Client is callable."""
    assert callable(Client)


def test_client_has_all_modules():
    """Test that both client types have all expected modules."""
    sync_client = Client(
        "https://api.example.com",
        "test-key",
        "test-site",
        "test-app",
        'sync'
    )

    async_client = Client(
        "https://api.example.com",
        "test-key",
        "test-site",
        "test-app",
        'async'
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
