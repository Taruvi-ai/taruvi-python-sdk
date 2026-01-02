"""
Auth API Module

Provides methods for:
- JWT token management
- User authentication
- Token refresh
- User CRUD operations
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional
from urllib.parse import urlencode

from taruvi.models.auth import TokenResponse, UserResponse, UserListResponse
from taruvi.models.app import UserApp

if TYPE_CHECKING:
    from taruvi.client import Client
    from taruvi.sync_client import SyncClient


# ============================================================================
# Shared Implementation Logic
# ============================================================================

def _build_login_request(username: str, password: str) -> tuple[str, dict[str, str]]:
    """Build login request."""
    return "/api/cloud/auth/jwt/token/", {"username": username, "password": password}


def _build_refresh_request(refresh_token: str) -> tuple[str, dict[str, str]]:
    """Build token refresh request."""
    return "/api/cloud/auth/jwt/token/refresh/", {"refresh": refresh_token}


def _build_verify_request(token: str) -> tuple[str, dict[str, str]]:
    """Build token verify request."""
    return "/api/cloud/auth/jwt/token/verify/", {"token": token}


def _build_user_create_request(
    username: str,
    email: str,
    password: str,
    confirm_password: str,
    first_name: Optional[str],
    last_name: Optional[str],
    is_active: bool,
    is_staff: bool,
    attributes: Optional[str]
) -> tuple[str, dict[str, Any]]:
    """Build user creation request."""
    body: dict[str, Any] = {
        "username": username,
        "email": email,
        "password": password,
        "confirm_password": confirm_password,
        "is_active": is_active,
        "is_staff": is_staff,
    }
    if first_name:
        body["first_name"] = first_name
    if last_name:
        body["last_name"] = last_name
    if attributes:
        body["attributes"] = attributes

    return "/api/users/", body


def _build_user_update_request(
    username: str,
    email: Optional[str],
    password: Optional[str],
    confirm_password: Optional[str],
    first_name: Optional[str],
    last_name: Optional[str],
    is_active: Optional[bool],
    is_staff: Optional[bool],
    attributes: Optional[str]
) -> tuple[str, dict[str, Any]]:
    """Build user update request."""
    body: dict[str, Any] = {}

    if email is not None:
        body["email"] = email
    if password is not None:
        body["password"] = password
    if confirm_password is not None:
        body["confirm_password"] = confirm_password
    if first_name is not None:
        body["first_name"] = first_name
    if last_name is not None:
        body["last_name"] = last_name
    if is_active is not None:
        body["is_active"] = is_active
    if is_staff is not None:
        body["is_staff"] = is_staff
    if attributes is not None:
        body["attributes"] = attributes

    return f"/api/users/{username}/", body


def _build_user_list_path(
    search: Optional[str],
    is_active: Optional[bool],
    is_staff: Optional[bool],
    is_superuser: Optional[bool],
    is_deleted: Optional[bool],
    ordering: Optional[str],
    page: Optional[int],
    page_size: Optional[int]
) -> str:
    """Build user list request path with query params."""
    path = "/api/users/"
    filters: dict[str, Any] = {}

    if search is not None:
        filters["search"] = search
    if is_active is not None:
        filters["is_active"] = is_active
    if is_staff is not None:
        filters["is_staff"] = is_staff
    if is_superuser is not None:
        filters["is_superuser"] = is_superuser
    if is_deleted is not None:
        filters["is_deleted"] = is_deleted
    if ordering is not None:
        filters["ordering"] = ordering
    if page is not None:
        filters["page"] = page
    if page_size is not None:
        filters["page_size"] = page_size

    if filters:
        path += "?" + urlencode(filters)

    return path


def _parse_user_apps(response: Any) -> list[UserApp]:
    """Parse user apps response."""
    if isinstance(response, list):
        return [UserApp.from_dict(app) for app in response]
    else:
        apps_list = response.get("data", [])
        return [UserApp.from_dict(app) for app in apps_list]


# ============================================================================
# Async Implementation
# ============================================================================

class AuthModule:
    """Authentication API operations."""

    def __init__(self, client: "Client") -> None:
        """Initialize Auth module."""
        self.client = client
        self._http = client._http_client
        self._config = client._config

    async def login(self, username: str, password: str) -> TokenResponse:
        """
        Login with username and password to get JWT tokens.

        Args:
            username: Username or email
            password: Password

        Returns:
            TokenResponse: JWT tokens (access and refresh)

        Example:
            ```python
            tokens = await client.auth.login("alice@example.com", "password123")
            print(f"Access token: {tokens.access}")
            ```
        """
        path, body = _build_login_request(username, password)
        response = await self._http.post(path, json=body)
        return TokenResponse.from_dict(response)

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            TokenResponse: New access token
        """
        path, body = _build_refresh_request(refresh_token)
        response = await self._http.post(path, json=body)
        return TokenResponse.from_dict(response)

    async def verify_token(self, token: str) -> dict[str, Any]:
        """
        Verify JWT token validity.

        Args:
            token: JWT token to verify

        Returns:
            dict: Verification result
        """
        path, body = _build_verify_request(token)
        response = await self._http.post(path, json=body)
        return response

    async def get_current_user(self) -> UserResponse:
        """
        Get current authenticated user details.

        Returns:
            UserResponse: User details
        """
        response = await self._http.get("/api/users/me/")
        return UserResponse.from_dict(response)

    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        confirm_password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        is_active: bool = True,
        is_staff: bool = False,
        attributes: Optional[str] = None
    ) -> UserResponse:
        """Create a new user."""
        path, body = _build_user_create_request(
            username, email, password, confirm_password,
            first_name, last_name, is_active, is_staff, attributes
        )
        response = await self._http.post(path, json=body)
        return UserResponse.from_dict(response)

    async def update_user(
        self,
        username: str,
        email: Optional[str] = None,
        password: Optional[str] = None,
        confirm_password: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_staff: Optional[bool] = None,
        attributes: Optional[str] = None
    ) -> UserResponse:
        """Update an existing user."""
        path, body = _build_user_update_request(
            username, email, password, confirm_password,
            first_name, last_name, is_active, is_staff, attributes
        )
        response = await self._http.put(path, json=body)
        return UserResponse.from_dict(response)

    async def delete_user(self, username: str) -> None:
        """Delete a user."""
        await self._http.delete(f"/api/users/{username}/")

    async def list_users(
        self,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_staff: Optional[bool] = None,
        is_superuser: Optional[bool] = None,
        is_deleted: Optional[bool] = None,
        ordering: Optional[str] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None
    ) -> UserListResponse:
        """List users with optional filters."""
        path = _build_user_list_path(
            search, is_active, is_staff, is_superuser,
            is_deleted, ordering, page, page_size
        )
        response = await self._http.get(path)
        return UserListResponse.from_dict(response)

    async def get_user_apps(self, username: str) -> list[UserApp]:
        """Get apps associated with a user."""
        response = await self._http.get(f"/api/users/{username}/apps/")
        return _parse_user_apps(response)


# ============================================================================
# Sync Implementation
# ============================================================================

class SyncAuthModule:
    """Synchronous Authentication API operations (native blocking)."""

    def __init__(self, client: "SyncClient") -> None:
        """Initialize synchronous Auth module."""
        self.client = client
        self._http = client._http
        self._config = client._config

    def login(self, username: str, password: str) -> TokenResponse:
        """Login with username and password to get JWT tokens (blocking)."""
        path, body = _build_login_request(username, password)
        response = self._http.post(path, json=body)
        return TokenResponse.from_dict(response)

    def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token (blocking)."""
        path, body = _build_refresh_request(refresh_token)
        response = self._http.post(path, json=body)
        return TokenResponse.from_dict(response)

    def verify_token(self, token: str) -> dict[str, Any]:
        """Verify JWT token validity (blocking)."""
        path, body = _build_verify_request(token)
        response = self._http.post(path, json=body)
        return response

    def get_current_user(self) -> UserResponse:
        """Get current authenticated user details (blocking)."""
        response = self._http.get("/api/users/me/")
        return UserResponse.from_dict(response)

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        confirm_password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        is_active: bool = True,
        is_staff: bool = False,
        attributes: Optional[str] = None
    ) -> UserResponse:
        """Create a new user (blocking)."""
        path, body = _build_user_create_request(
            username, email, password, confirm_password,
            first_name, last_name, is_active, is_staff, attributes
        )
        response = self._http.post(path, json=body)
        return UserResponse.from_dict(response)

    def update_user(
        self,
        username: str,
        email: Optional[str] = None,
        password: Optional[str] = None,
        confirm_password: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_staff: Optional[bool] = None,
        attributes: Optional[str] = None
    ) -> UserResponse:
        """Update an existing user (blocking)."""
        path, body = _build_user_update_request(
            username, email, password, confirm_password,
            first_name, last_name, is_active, is_staff, attributes
        )
        response = self._http.put(path, json=body)
        return UserResponse.from_dict(response)

    def delete_user(self, username: str) -> None:
        """Delete a user (blocking)."""
        self._http.delete(f"/api/users/{username}/")

    def list_users(
        self,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_staff: Optional[bool] = None,
        is_superuser: Optional[bool] = None,
        is_deleted: Optional[bool] = None,
        ordering: Optional[str] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None
    ) -> UserListResponse:
        """List users with optional filters (blocking)."""
        path = _build_user_list_path(
            search, is_active, is_staff, is_superuser,
            is_deleted, ordering, page, page_size
        )
        response = self._http.get(path)
        return UserListResponse.from_dict(response)

    def get_user_apps(self, username: str) -> list[UserApp]:
        """Get apps associated with a user (blocking)."""
        response = self._http.get(f"/api/users/{username}/apps/")
        return _parse_user_apps(response)
