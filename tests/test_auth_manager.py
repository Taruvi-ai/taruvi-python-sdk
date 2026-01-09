"""
Unit tests for Auth Module (client.auth) - NO MOCKS.

Tests the authentication refactoring that separates project-level configuration
from user-level authentication.

Auth functionality is now provided by AuthModule (accessed via client.auth).
AuthManager has been merged into AuthModule.

These tests do NOT use mocks - they test real logic without external dependencies.
For tests that require real HTTP calls (login, token refresh), see test_auth_integration.py
"""

import pytest
import concurrent.futures
from taruvi import Client
from taruvi.exceptions import NotAuthenticatedError


# ============================================================================
# Client Creation Tests - New Auth Pattern
# ============================================================================

def test_client_created_without_auth(unauth_test_config):
    """Test that Client can be created without authentication parameters."""
    client = Client(
        api_url=unauth_test_config["api_url"],
        app_slug=unauth_test_config["app_slug"],
        mode='sync'
    )

    # Verify it's a sync client by checking for _http_client attribute
    assert hasattr(client, '_http_client'), "Sync client should have _http_client attribute"
    assert not client.is_authenticated
    assert client._config.jwt is None
    assert client._config.api_key is None
    assert client._config.session_token is None


def test_async_client_created_without_auth(unauth_test_config):
    """Test that async Client can be created without authentication parameters."""
    client = Client(
        api_url=unauth_test_config["api_url"],
        app_slug=unauth_test_config["app_slug"],
        mode='async'
    )

    # Verify it's an async client by checking for async-specific attributes
    assert hasattr(client, '_http_client'), "Async client should have _http_client attribute"
    assert not client.is_authenticated


def test_client_has_auth_property(unauth_test_config):
    """Test that Client has auth property returning AuthModule."""
    client = Client(
        api_url=unauth_test_config["api_url"],
        app_slug=unauth_test_config["app_slug"]
    )

    assert hasattr(client, 'auth')
    # Auth module should have all required methods
    assert hasattr(client.auth, 'signInWithPassword')
    assert hasattr(client.auth, 'signInWithToken')
    assert hasattr(client.auth, 'signOut')
    assert hasattr(client.auth, 'get_current_user')


def test_client_has_is_authenticated_property(unauth_test_config):
    """Test that Client has is_authenticated property."""
    client = Client(
        api_url=unauth_test_config["api_url"],
        app_slug=unauth_test_config["app_slug"]
    )

    assert hasattr(client, 'is_authenticated')
    assert isinstance(client.is_authenticated, bool)
    assert client.is_authenticated is False


# ============================================================================
# AuthManager - signInWithToken Tests
# ============================================================================

def test_sign_in_with_jwt_token(unauth_test_config):
    """Test JWT Bearer authentication via signInWithToken."""
    client = Client(
        api_url=unauth_test_config["api_url"],
        app_slug=unauth_test_config["app_slug"]
    )

    # Sign in with JWT
    auth_client = client.auth.signInWithToken(
        token='eyJhbGci_test_jwt_token',
        token_type='jwt'
    )

    # Verify new client returned
    assert auth_client is not client
    # Verify auth_client is a sync client
    assert hasattr(auth_client, '_http_client'), "Sync client should have _http_client attribute"

    # Verify authentication
    assert auth_client.is_authenticated
    assert auth_client._config.jwt == 'eyJhbGci_test_jwt_token'
    assert auth_client._config.api_key is None
    assert auth_client._config.session_token is None

    # Verify headers
    assert 'Authorization' in auth_client._config.headers
    assert auth_client._config.headers['Authorization'] == 'Bearer eyJhbGci_test_jwt_token'


def test_sign_in_with_api_key(unauth_test_config):
    """Test Knox API Key authentication via signInWithToken."""
    client = Client(
        api_url=unauth_test_config["api_url"],
        app_slug=unauth_test_config["app_slug"]
    )

    # Sign in with API key
    auth_client = client.auth.signInWithToken(
        token='knox_api_key_abc123',
        token_type='api_key'
    )

    # Verify authentication
    assert auth_client.is_authenticated
    assert auth_client._config.api_key == 'knox_api_key_abc123'
    assert auth_client._config.jwt is None

    # Verify headers
    assert auth_client._config.headers['Authorization'] == 'Api-Key knox_api_key_abc123'


def test_sign_in_with_session_token(unauth_test_config):
    """Test session token authentication via signInWithToken."""
    client = Client(
        api_url=unauth_test_config["api_url"],
        app_slug=unauth_test_config["app_slug"]
    )

    # Sign in with session token
    auth_client = client.auth.signInWithToken(
        token='session_token_xyz789',
        token_type='session_token'
    )

    # Verify authentication
    assert auth_client.is_authenticated
    assert auth_client._config.session_token == 'session_token_xyz789'
    assert auth_client._config.jwt is None
    assert auth_client._config.api_key is None

    # Verify headers
    assert 'X-Session-Token' in auth_client._config.headers
    assert auth_client._config.headers['X-Session-Token'] == 'session_token_xyz789'


def test_sign_in_with_invalid_token_type(unauth_test_config):
    """Test that invalid token_type raises ValueError."""
    client = Client(
        api_url=unauth_test_config["api_url"],
        app_slug=unauth_test_config["app_slug"]
    )

    with pytest.raises(ValueError, match="Invalid token_type"):
        client.auth.signInWithToken(
            token='some_token',
            token_type='invalid_type'
        )


def test_sign_in_with_token_defaults_to_jwt(unauth_test_config):
    """Test that signInWithToken defaults to jwt token_type."""
    client = Client(
        api_url=unauth_test_config["api_url"],
        app_slug=unauth_test_config["app_slug"]
    )

    # Don't specify token_type, should default to 'jwt'
    auth_client = client.auth.signInWithToken(token='test_token')

    assert auth_client._config.jwt == 'test_token'
    assert auth_client._config.headers['Authorization'] == 'Bearer test_token'


# ============================================================================
# AuthManager - signOut Tests
# ============================================================================

def test_sign_out(unauth_test_config):
    """Test sign out removes authentication."""
    client = Client(
        api_url=unauth_test_config["api_url"],
        app_slug=unauth_test_config["app_slug"]
    )

    # Sign in first
    auth_client = client.auth.signInWithToken(
        token='test_jwt_token',
        token_type='jwt'
    )

    assert auth_client.is_authenticated

    # Sign out
    unauth_client = auth_client.auth.signOut()

    # Verify new unauthenticated client
    assert unauth_client is not auth_client
    assert not unauth_client.is_authenticated
    assert unauth_client._config.jwt is None
    assert unauth_client._config.api_key is None
    assert unauth_client._config.session_token is None

    # Verify original auth_client unchanged
    assert auth_client.is_authenticated


# ============================================================================
# Immutability Tests
# ============================================================================

def test_auth_returns_new_client_instance(unauth_test_config):
    """Test that auth methods return new client instances (immutability)."""
    client = Client(
        api_url=unauth_test_config["api_url"],
        app_slug=unauth_test_config["app_slug"]
    )

    auth_client = client.auth.signInWithToken(token='test_token', token_type='jwt')

    # Should be different objects
    assert client is not auth_client
    assert id(client) != id(auth_client)


def test_original_client_unchanged_after_auth(unauth_test_config):
    """Test that original client remains unchanged after authentication."""
    client = Client(
        api_url=unauth_test_config["api_url"],
        app_slug=unauth_test_config["app_slug"]
    )

    # Store original state
    original_jwt = client._config.jwt
    original_authenticated = client.is_authenticated

    # Authenticate (creates new client)
    auth_client = client.auth.signInWithToken(token='test_token', token_type='jwt')

    # Original client unchanged
    assert client._config.jwt == original_jwt
    assert client.is_authenticated == original_authenticated
    assert not client.is_authenticated

    # New client authenticated
    assert auth_client.is_authenticated
    assert auth_client._config.jwt == 'test_token'


def test_chain_auth_operations(unauth_test_config):
    """Test chaining multiple auth operations creates new clients each time."""
    client = Client(
        api_url=unauth_test_config["api_url"],
        app_slug=unauth_test_config["app_slug"]
    )

    # Sign in with JWT
    jwt_client = client.auth.signInWithToken(token='jwt1', token_type='jwt')
    assert jwt_client._config.jwt == 'jwt1'
    assert jwt_client._config.api_key is None

    # Switch to API key (creates new client)
    apikey_client = jwt_client.auth.signInWithToken(token='key1', token_type='api_key')
    assert apikey_client._config.api_key == 'key1'
    assert apikey_client._config.jwt is None  # JWT should be removed

    # Original clients unchanged
    assert jwt_client._config.jwt == 'jwt1'
    assert not client.is_authenticated

    # Sign out
    unauth_client = apikey_client.auth.signOut()
    assert not unauth_client.is_authenticated

    # All different instances
    assert client is not jwt_client
    assert jwt_client is not apikey_client
    assert apikey_client is not unauth_client


# ============================================================================
# Thread Safety Tests
# ============================================================================

def test_concurrent_auth_from_same_base_client(unauth_test_config):
    """Test thread safety - multiple auths from same base client."""
    base_client = Client(
        api_url=unauth_test_config["api_url"],
        app_slug=unauth_test_config["app_slug"]
    )

    def auth_user(user_id):
        return base_client.auth.signInWithToken(
            token=f'user_{user_id}_jwt',
            token_type='jwt'
        )

    # Create 10 authenticated clients concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(auth_user, i) for i in range(10)]
        clients = [f.result() for f in futures]

    # Each should be a different instance
    client_ids = [id(c) for c in clients]
    assert len(set(client_ids)) == 10, "All clients should be unique instances"

    # Each should have correct authentication
    for i, client in enumerate(clients):
        assert client.is_authenticated
        assert client._config.jwt == f'user_{i}_jwt'

    # Base client unchanged
    assert not base_client.is_authenticated


# ============================================================================
# NotAuthenticatedError Tests
# ============================================================================

def test_not_authenticated_error_exists(unauth_test_config):
    """Test that NotAuthenticatedError exception is available."""
    from taruvi.exceptions import NotAuthenticatedError

    error = NotAuthenticatedError("Test message")
    assert error.status_code == 401
    assert "Test message" in str(error)


def test_http_client_checks_authentication(unauth_test_config):
    """Test that async HTTP client has authentication checking."""
    from taruvi._async.http_client import AsyncHTTPClient
    from taruvi.config import TaruviConfig

    config = TaruviConfig(
        api_url=unauth_test_config["api_url"],
        app_slug=unauth_test_config["app_slug"]
    )

    http_client = AsyncHTTPClient(config)

    # Should have _is_client_authenticated method
    assert hasattr(http_client, '_is_client_authenticated')
    assert callable(http_client._is_client_authenticated)

    # Should return False for unauthenticated client
    assert http_client._is_client_authenticated() is False


def test_sync_http_client_checks_authentication(unauth_test_config):
    """Test that sync HTTP client has authentication checking."""
    from taruvi._sync.http_client import HTTPClient
    from taruvi.config import TaruviConfig

    config = TaruviConfig(
        api_url=unauth_test_config["api_url"],
        app_slug=unauth_test_config["app_slug"]
    )

    sync_http_client = HTTPClient(config)

    # Should have _is_client_authenticated method
    assert hasattr(sync_http_client, '_is_client_authenticated')
    assert callable(sync_http_client._is_client_authenticated)

    # Should return False for unauthenticated client
    assert sync_http_client._is_client_authenticated() is False


# ============================================================================
# is_authenticated Property Tests
# ============================================================================

def test_is_authenticated_false_initially(unauth_test_config):
    """Test that is_authenticated is False for unauthenticated client."""
    client = Client(
        api_url=unauth_test_config["api_url"],
        app_slug=unauth_test_config["app_slug"]
    )

    assert client.is_authenticated is False


def test_is_authenticated_true_after_jwt_auth(unauth_test_config):
    """Test that is_authenticated is True after JWT authentication."""
    client = Client(
        api_url=unauth_test_config["api_url"],
        app_slug=unauth_test_config["app_slug"]
    )

    auth_client = client.auth.signInWithToken(token='jwt', token_type='jwt')
    assert auth_client.is_authenticated is True


def test_is_authenticated_true_after_api_key_auth(unauth_test_config):
    """Test that is_authenticated is True after API key authentication."""
    client = Client(
        api_url=unauth_test_config["api_url"],
        app_slug=unauth_test_config["app_slug"]
    )

    auth_client = client.auth.signInWithToken(token='api_key', token_type='api_key')
    assert auth_client.is_authenticated is True


def test_is_authenticated_true_after_session_token_auth(unauth_test_config):
    """Test that is_authenticated is True after session token authentication."""
    client = Client(
        api_url=unauth_test_config["api_url"],
        app_slug=unauth_test_config["app_slug"]
    )

    auth_client = client.auth.signInWithToken(token='session', token_type='session_token')
    assert auth_client.is_authenticated is True


def test_is_authenticated_false_after_sign_out(unauth_test_config):
    """Test that is_authenticated is False after sign out."""
    client = Client(
        api_url=unauth_test_config["api_url"],
        app_slug=unauth_test_config["app_slug"]
    )

    auth_client = client.auth.signInWithToken(token='jwt', token_type='jwt')
    assert auth_client.is_authenticated is True

    unauth_client = auth_client.auth.signOut()
    assert unauth_client.is_authenticated is False


# ============================================================================
# Async Client Auth Tests
# ============================================================================

def test_async_client_auth_pattern(unauth_test_config):
    """Test auth pattern works with async client."""
    client = Client(
        api_url=unauth_test_config["api_url"],
        app_slug=unauth_test_config["app_slug"],
        mode='async'
    )

    # Verify it's an async client by checking for async-specific attributes
    assert hasattr(client, '_http_client'), "Async client should have _http_client attribute"
    assert not client.is_authenticated

    # Authenticate
    auth_client = client.auth.signInWithToken(token='async_jwt', token_type='jwt')

    # Verify auth_client is an async client
    assert hasattr(auth_client, '_http_client'), "Async client should have _http_client attribute"
    assert auth_client.is_authenticated
    assert auth_client._config.jwt == 'async_jwt'


def test_async_client_sign_out(unauth_test_config):
    """Test async client sign out."""
    client = Client(
        api_url=unauth_test_config["api_url"],
        app_slug=unauth_test_config["app_slug"],
        mode='async'
    )

    auth_client = client.auth.signInWithToken(token='jwt', token_type='jwt')
    unauth_client = auth_client.auth.signOut()

    # Verify unauth_client is an async client
    assert hasattr(unauth_client, '_http_client'), "Async client should have _http_client attribute"
    assert not unauth_client.is_authenticated


# ============================================================================
# Module Reinitialization Tests
# ============================================================================

def test_modules_reinitialize_with_new_auth(unauth_test_config):
    """Test that lazy-loaded modules reinitialize with new authentication."""
    client = Client(
        api_url=unauth_test_config["api_url"],
        app_slug=unauth_test_config["app_slug"]
    )

    # Access a module to trigger lazy loading
    _ = client.database

    # Authenticate (creates new client)
    auth_client = client.auth.signInWithToken(token='jwt', token_type='jwt')

    # Modules should be reset to None, will reinitialize on first access
    assert auth_client._database is None
    assert auth_client._functions is None
    assert auth_client._storage is None

    # Access module on auth_client should work
    _ = auth_client.database
    assert auth_client._database is not None


# ============================================================================
# Additional Auth Flow Tests
# ============================================================================

def test_multiple_auth_switches(unauth_test_config):
    """Test switching between different authentication types."""
    client = Client(
        api_url=unauth_test_config["api_url"],
        app_slug=unauth_test_config["app_slug"]
    )

    # Start with JWT
    jwt_client = client.auth.signInWithToken(token='jwt_token', token_type='jwt')
    assert jwt_client._config.jwt == 'jwt_token'
    assert jwt_client._config.api_key is None
    assert jwt_client._config.session_token is None

    # Switch to session token
    session_client = jwt_client.auth.signInWithToken(token='session_token', token_type='session_token')
    assert session_client._config.session_token == 'session_token'
    assert session_client._config.jwt is None
    assert session_client._config.api_key is None

    # Switch to API key
    apikey_client = session_client.auth.signInWithToken(token='api_key', token_type='api_key')
    assert apikey_client._config.api_key == 'api_key'
    assert apikey_client._config.jwt is None
    assert apikey_client._config.session_token is None


def test_auth_with_both_sync_and_async(unauth_test_config):
    """Test that auth works identically for sync and async clients."""
    # Sync client
    sync_client = Client(
        api_url=unauth_test_config["api_url"],
        app_slug=unauth_test_config["app_slug"],
        mode='sync'
    )
    sync_auth = sync_client.auth.signInWithToken(token='test_token', token_type='jwt')

    # Async client
    async_client = Client(
        api_url=unauth_test_config["api_url"],
        app_slug=unauth_test_config["app_slug"],
        mode='async'
    )
    async_auth = async_client.auth.signInWithToken(token='test_token', token_type='jwt')

    # Both should be authenticated the same way
    assert sync_auth.is_authenticated == async_auth.is_authenticated
    assert sync_auth._config.jwt == async_auth._config.jwt
    assert sync_auth._config.headers['Authorization'] == async_auth._config.headers['Authorization']
