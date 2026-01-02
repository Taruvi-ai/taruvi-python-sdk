"""Test auth module - both async and sync."""

import pytest
from unittest.mock import AsyncMock

from taruvi.modules.auth import (
    AuthModule,
    SyncAuthModule,
    _build_login_request,
    _build_refresh_request,
    _build_user_create_request,
    _build_user_update_request,
    _build_user_list_path,
    _parse_user_apps
)


# ============================================================================
# Test Shared Helper Functions
# ============================================================================

def test_build_login_request():
    """Test login request builder."""
    path, body = _build_login_request("user@example.com", "password123")
    assert path == "/api/cloud/auth/jwt/token/"
    assert body == {"username": "user@example.com", "password": "password123"}


def test_build_refresh_request():
    """Test refresh token request builder."""
    path, body = _build_refresh_request("refresh_token_123")
    assert path == "/api/cloud/auth/jwt/token/refresh/"
    assert body == {"refresh": "refresh_token_123"}


def test_build_user_create_request():
    """Test user create request builder."""
    path, body = _build_user_create_request(
        "john_doe",
        "john@example.com",
        "pass123",
        "pass123",
        "John",
        "Doe",
        True,
        False,
        None
    )

    assert path == "/api/users/"
    assert body["username"] == "john_doe"
    assert body["email"] == "john@example.com"
    assert body["first_name"] == "John"
    assert body["last_name"] == "Doe"
    assert body["is_active"] is True
    assert body["is_staff"] is False


def test_build_user_update_request():
    """Test user update request builder."""
    path, body = _build_user_update_request(
        "john_doe",
        "newemail@example.com",
        None,
        None,
        "Jane",
        None,
        False,
        None,
        None
    )

    assert path == "/api/users/john_doe/"
    assert body["email"] == "newemail@example.com"
    assert body["first_name"] == "Jane"
    assert body["is_active"] is False
    assert "password" not in body


def test_build_user_list_path():
    """Test user list path builder."""
    path = _build_user_list_path(
        search="john",
        is_active=True,
        is_staff=None,
        is_superuser=None,
        is_deleted=False,
        ordering="-date_joined",
        page=2,
        page_size=20
    )

    assert "/api/users/" in path
    assert "search=john" in path
    assert "is_active=True" in path
    assert "is_deleted=False" in path
    assert "ordering=-date_joined" in path
    assert "page=2" in path
    assert "page_size=20" in path


def test_parse_user_apps_list():
    """Test parsing user apps from list response."""
    response = [
        {"id": 1, "name": "App 1", "slug": "app-1"},
        {"id": 2, "name": "App 2", "slug": "app-2"}
    ]

    apps = _parse_user_apps(response)
    assert len(apps) == 2
    assert apps[0].slug == "app-1"
    assert apps[1].slug == "app-2"


def test_parse_user_apps_dict():
    """Test parsing user apps from dict response."""
    response = {
        "data": [
            {"id": 1, "name": "App 1", "slug": "app-1"}
        ]
    }

    apps = _parse_user_apps(response)
    assert len(apps) == 1
    assert apps[0].slug == "app-1"


# ============================================================================
# Test Async AuthModule
# ============================================================================

@pytest.mark.asyncio
async def test_auth_module_login(mock_async_client):
    """Test async login method."""
    auth = AuthModule(mock_async_client)

    # Mock response
    mock_async_client._http_client.post.return_value = {
        "access": "access_token_123",
        "refresh": "refresh_token_123"
    }

    result = await auth.login("user@example.com", "password123")

    # Verify HTTP call was made correctly
    mock_async_client._http_client.post.assert_called_once()
    call_args = mock_async_client._http_client.post.call_args
    assert call_args[0][0] == "/api/cloud/auth/jwt/token/"
    assert call_args[1]["json"]["username"] == "user@example.com"
    assert call_args[1]["json"]["password"] == "password123"

    # Verify result
    assert result.access == "access_token_123"
    assert result.refresh == "refresh_token_123"


@pytest.mark.asyncio
async def test_auth_module_get_current_user(mock_async_client):
    """Test async get current user method."""
    auth = AuthModule(mock_async_client)

    # Mock response
    mock_async_client._http_client.get.return_value = {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe"
    }

    result = await auth.get_current_user()

    # Verify HTTP call
    mock_async_client._http_client.get.assert_called_once_with("/api/users/me/")

    # Verify result
    assert result.username == "john_doe"
    assert result.email == "john@example.com"


# ============================================================================
# Test Sync AuthModule
# ============================================================================

def test_sync_auth_module_login(mock_sync_client):
    """Test sync login method."""
    auth = SyncAuthModule(mock_sync_client)

    # Mock response
    mock_sync_client._http.post.return_value = {
        "access": "access_token_123",
        "refresh": "refresh_token_123"
    }

    result = auth.login("user@example.com", "password123")

    # Verify HTTP call was made correctly
    mock_sync_client._http.post.assert_called_once()
    call_args = mock_sync_client._http.post.call_args
    assert call_args[0][0] == "/api/cloud/auth/jwt/token/"
    assert call_args[1]["json"]["username"] == "user@example.com"

    # Verify result
    assert result.access == "access_token_123"
    assert result.refresh == "refresh_token_123"


def test_sync_auth_module_get_current_user(mock_sync_client):
    """Test sync get current user method."""
    auth = SyncAuthModule(mock_sync_client)

    # Mock response
    mock_sync_client._http.get.return_value = {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe"
    }

    result = auth.get_current_user()

    # Verify HTTP call
    mock_sync_client._http.get.assert_called_once_with("/api/users/me/")

    # Verify result
    assert result.username == "john_doe"
    assert result.email == "john@example.com"


# ============================================================================
# Test Sync/Async Equivalence
# ============================================================================

def test_async_sync_equivalence(mock_async_client, mock_sync_client):
    """Test that async and sync modules have the same methods."""
    async_auth = AuthModule(mock_async_client)
    sync_auth = SyncAuthModule(mock_sync_client)

    # Get public methods
    async_methods = {m for m in dir(async_auth) if not m.startswith('_')}
    sync_methods = {m for m in dir(sync_auth) if not m.startswith('_')}

    # Should have the same public API
    assert async_methods == sync_methods
