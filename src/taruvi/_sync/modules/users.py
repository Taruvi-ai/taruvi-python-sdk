"""
Users API Module

Provides methods for:
- User CRUD operations
- User management
- Role assignment and revocation
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from taruvi.modules.base import BaseModule
from taruvi.utils import build_query_string, build_params
from taruvi.types import User

if TYPE_CHECKING:
    from taruvi._sync.client import SyncClient


# ============================================================================
# Shared Implementation Logic
# ============================================================================

def _build_get_user_path(username: str) -> str:
    """Build get user request path."""
    return f"/api/users/{username}/"


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


def _build_user_list_path(**kwargs: Any) -> str:
    """Build user list request path with query params."""
    return f"/api/users/{build_query_string(build_params(**kwargs))}"


def _build_assign_roles_request(
    roles: list[str],
    usernames: list[str],
    expires_at: Optional[str]
) -> tuple[str, dict[str, Any]]:
    """Build bulk assign roles request."""
    body: dict[str, Any] = {
        "roles": roles,
        "usernames": usernames
    }
    if expires_at is not None:
        body["expires_at"] = expires_at

    return "/api/assign/roles/", body


def _build_revoke_roles_request(
    roles: list[str],
    usernames: list[str]
) -> tuple[str, dict[str, Any]]:
    """Build bulk revoke roles request."""
    body: dict[str, Any] = {
        "roles": roles,
        "usernames": usernames
    }

    return "/api/revoke/roles/", body


# ============================================================================
# Sync Implementation
# ============================================================================

class UsersModule(BaseModule):
    """User management API operations."""

    def __init__(self, client: "SyncClient") -> None:
        """Initialize Users module."""
        self.client = client
        super().__init__(client._http_client, client._config)

    def get(self, username: str) -> User:
        """
        Get user details by username.

        Args:
            username: Username to retrieve

        Returns:
            User dict with id, email, username, etc.

        Example:
            ```python
            user = client.users.get("alice")
            print(f"Email: {user['data']['email']}")
            ```
        """
        path = _build_get_user_path(username)
        response = self._http.get(path)
        return response

    def create(self, data: dict[str, Any]) -> User:
        """
        Create a new user.

        Args:
            data: Dict with user fields. Required keys:
                  username, email, password, confirm_password
                  Optional: first_name, last_name, is_active, is_staff, attributes

        Returns:
            User dict with created user details

        Example:
            ```python
            user = client.users.create({
                "username": "alice",
                "email": "alice@example.com",
                "password": "secure123",
                "confirm_password": "secure123",
                "first_name": "Alice",
                "last_name": "Smith"
            })
            ```
        """
        response = self._http.post("/api/users/", json=data)
        return response

    def update(
        self,
        username: str,
        data: dict[str, Any],
    ) -> User:
        """
        Update an existing user.

        Args:
            username: Username of user to update
            data: Dict with fields to update. Supported keys:
                  email, password, confirm_password, first_name,
                  last_name, is_active, is_staff, attributes

        Returns:
            User dict with updated user details

        Example:
            ```python
            user = client.users.update("alice", {
                "email": "newemail@example.com",
                "first_name": "Alice",
                "is_active": False
            })
            ```
        """
        path = f"/api/users/{username}/"
        response = self._http.put(path, json=data)
        return response

    def delete(self, username: str) -> None:
        """
        Delete a user.

        Args:
            username: Username of user to delete

        Example:
            ```python
            client.users.delete("alice")
            ```
        """
        self._http.delete(f"/api/users/{username}/")

    def list(self, **kwargs: Any) -> dict[str, Any]:
        """
        List users with optional filters.

        Supports all API query parameters as keyword arguments:
            search: Search by username/email/name
            is_active: Filter by active status
            is_staff: Filter by staff status
            is_superuser: Filter by superuser status
            is_deleted: Filter by deleted status
            is_cloud_user: Filter by cloud user status
            roles: Comma-separated role slugs (e.g., "admin,manager")
            ordering: Sort field (e.g., "-date_joined")
            page: Page number
            page_size: Items per page
            **kwargs: Reference attribute filters (e.g., department_id=123)

        Returns:
            dict: User list response with pagination

        Example:
            ```python
            users = client.users.list(
                is_active=True,
                roles="admin",
                department_id=123,
                page=1,
                page_size=20
            )
            for user in users["results"]:
                print(user["username"])
            ```
        """
        path = _build_user_list_path(**kwargs)
        response = self._http.get(path)
        return response

    def apps(self, username: str) -> list[dict[str, Any]]:
        """
        Get apps associated with a user.

        Args:
            username: Username to get apps for

        Returns:
            list: List of apps

        Example:
            ```python
            apps = client.users.apps("alice")
            for app in apps:
                print(app["slug"])
            ```
        """
        response = self._http.get(f"/api/users/{username}/apps/")
        return self._extract_data_list(response)

    def assign_roles(
        self,
        roles: list[str],
        usernames: list[str],
        expires_at: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Bulk assign roles to users.

        Args:
            roles: List of role slugs to assign (max 100)
            usernames: List of usernames to assign roles to (max 100)
            expires_at: Optional ISO 8601 timestamp for role expiration

        Returns:
            dict: Assignment result response

        Example:
            ```python
            # Assign multiple roles to multiple users
            result = client.users.assign_roles(
                roles=["admin", "manager"],
                usernames=["alice", "bob"],
                expires_at="2025-06-15T23:59:59Z"  # Optional
            )
            print(result["message"])  # "Assigned 4 roles successfully"

            # Permanent assignment (no expiration)
            result = client.users.assign_roles(
                roles=["viewer"],
                usernames=["charlie"]
            )
            ```

        Note:
            - Can mix AppRole and SiteRole slugs
            - Creates UserRoleMembership records
            - Max 100 roles and 100 usernames per request
        """
        path, body = _build_assign_roles_request(roles, usernames, expires_at)
        response = self._http.post(path, json=body)
        return response

    def get_preferences(self) -> dict[str, Any]:
        """
        Get current user's preferences. Auto-creates with defaults if not exists.

        Returns:
            dict with date_format, time_format, timezone, theme, widget_config

        Example:
            ```python
            prefs = client.users.get_preferences()
            print(prefs["data"]["theme"])
            ```
        """
        return self._http.get("/api/users/me/preferences/")

    def update_preferences(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Create or update current user's preferences (upsert).

        Args:
            data: Preference fields to update:
                - date_format: "YYYY-MM-DD", "DD/MM/YYYY", "MM/DD/YYYY", "DD-MMM-YYYY"
                - time_format: "24h", "12h"
                - timezone: IANA timezone (e.g. "Asia/Kolkata")
                - theme: "light", "dark"
                - widget_config: dict with arbitrary UI config

        Returns:
            dict with updated preference data

        Example:
            ```python
            prefs = client.users.update_preferences({"theme": "dark", "timezone": "Asia/Kolkata"})
            ```
        """
        return self._http.put("/api/users/me/preferences/", json=data)

    def revoke_roles(
        self,
        roles: list[str],
        usernames: list[str]
    ) -> dict[str, Any]:
        """
        Bulk revoke roles from users.

        Args:
            roles: List of role slugs to revoke (max 100)
            usernames: List of usernames to revoke roles from (max 100)

        Returns:
            dict: Revocation result response

        Example:
            ```python
            # Revoke multiple roles from multiple users
            result = client.users.revoke_roles(
                roles=["admin", "manager"],
                usernames=["alice", "bob"]
            )
            print(result["message"])  # "Revoked 4 roles successfully"
            ```

        Note:
            - Works with both AppRole and SiteRole
            - Deletes UserRoleMembership records
            - Max 100 roles and 100 usernames per request
        """
        path, body = _build_revoke_roles_request(roles, usernames)
        # Use request() directly as delete() convenience method doesn't support JSON body
        response = self._http.request("DELETE", path, json=body)
        return response

