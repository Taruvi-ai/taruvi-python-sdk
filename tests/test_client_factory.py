"""Test the unified Client factory function (v0.2.0+)."""

import pytest
from taruvi import Client


def test_client_defaults_to_sync(unauth_test_config):
    """Test that Client() without mode defaults to sync."""
    client = Client(
        api_url=unauth_test_config["api_url"],
        app_slug=unauth_test_config["app_slug"]
    )
    # Verify it's a sync client by checking for _http_client attribute
    assert hasattr(client, '_http_client'), "Sync client should have _http_client attribute"
    assert not hasattr(client, '__aenter__'), "Sync client should not be async context manager"


def test_client_explicit_sync_mode(unauth_test_config):
    """Test that Client(mode='sync') returns sync client."""
    client = Client(
        api_url=unauth_test_config["api_url"],
        app_slug=unauth_test_config["app_slug"],
        mode='sync'
    )
    # Verify it's a sync client
    assert hasattr(client, '_http_client'), "Sync client should have _http_client attribute"
    assert hasattr(client, 'database'), "Client should have database module"
    assert hasattr(client, 'functions'), "Client should have functions module"


def test_client_async_mode():
    """Test that Client(mode='async') returns async client."""
    client = Client(
        api_url="https://api.example.com",
        app_slug="test-app",
        mode='async'
    )
    # Verify it's an async client
    assert hasattr(client, '_http_client'), "Async client should have _http_client attribute"
    assert hasattr(client, '__aenter__'), "Async client should be async context manager"
    assert hasattr(client, 'close'), "Async client should have close method"


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


def test_client_with_optional_params(unauth_test_config):
    """Test that Client accepts optional configuration parameters."""
    client = Client(
        api_url=unauth_test_config["api_url"],
        app_slug=unauth_test_config["app_slug"],
        mode='sync',
        timeout=60,
        max_retries=5
    )
    # Verify it's a sync client
    assert hasattr(client, '_http_client'), "Sync client should have _http_client attribute"
    # Verify configuration was applied
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
