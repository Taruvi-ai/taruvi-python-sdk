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
    from taruvi._async.client import AsyncClient


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


def _build_user_list_path(
    search: Optional[str],
    is_active: Optional[bool],
    is_staff: Optional[bool],
    is_superuser: Optional[bool],
    is_deleted: Optional[bool],
    roles: Optional[str],
    ordering: Optional[str],
    page: Optional[int],
    page_size: Optional[int]
) -> str:
    """Build user list request path with query params."""
    filters = build_params(
        search=search,
        is_active=is_active,
        is_staff=is_staff,
        is_superuser=is_superuser,
        is_deleted=is_deleted,
        roles=roles,
        ordering=ordering,
        page=page,
        page_size=page_size,
    )

    return f"/api/users/{build_query_string(filters)}"


def _parse_user_apps(response: Any) -> list[dict[str, Any]]:
    """Parse user apps response."""
    if isinstance(response, list):
        return response
    else:
        apps_list = response.get("data", [])
        return apps_list


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
# Async Implementation
# ============================================================================

class AsyncUsersModule(BaseModule):
    """User management API operations."""

    def __init__(self, client: "AsyncClient") -> None:
        """Initialize Users module."""
        self.client = client
        super().__init__(client._http_client, client._config)

    async def get_user(self, username: str) -> User:
        """
        Get user details by username.

        Args:
            username: Username to retrieve

        Returns:
            User dict with id, email, username, etc.

        Example:
            ```python
            user = await client.users.get_user("alice")
            print(f"Email: {user['data']['email']}")
            ```
        """
        path = _build_get_user_path(username)
        response = await self._http.get(path)
        return response

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
    ) -> User:
        """
        Create a new user.

        Args:
            username: Unique username
            email: User email address
            password: User password
            confirm_password: Password confirmation (must match password)
            first_name: Optional first name
            last_name: Optional last name
            is_active: Whether user is active (default: True)
            is_staff: Whether user is staff (default: False)
            attributes: Optional JSON string of custom attributes

        Returns:
            User dict with created user details

        Example:
            ```python
            user = await client.users.create_user(
                username="alice",
                email="alice@example.com",
                password="secure123",
                confirm_password="secure123",
                first_name="Alice",
                last_name="Smith"
            )
            ```
        """
        path, body = _build_user_create_request(
            username, email, password, confirm_password,
            first_name, last_name, is_active, is_staff, attributes
        )
        response = await self._http.post(path, json=body)
        return response

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
    ) -> User:
        """
        Update an existing user.

        Args:
            username: Username of user to update
            email: Updated email address
            password: New password
            confirm_password: Password confirmation
            first_name: Updated first name
            last_name: Updated last name
            is_active: Updated active status
            is_staff: Updated staff status
            attributes: Updated JSON string of custom attributes

        Returns:
            User dict with updated user details

        Example:
            ```python
            user = await client.users.update_user(
                username="alice",
                email="newemail@example.com",
                is_active=False
            )
            ```
        """
        path, body = _build_user_update_request(
            username, email, password, confirm_password,
            first_name, last_name, is_active, is_staff, attributes
        )
        response = await self._http.put(path, json=body)
        return response

    async def delete_user(self, username: str) -> None:
        """
        Delete a user.

        Args:
            username: Username of user to delete

        Example:
            ```python
            await client.users.delete_user("alice")
            ```
        """
        await self._http.delete(f"/api/users/{username}/")

    async def list_users(
        self,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_staff: Optional[bool] = None,
        is_superuser: Optional[bool] = None,
        is_deleted: Optional[bool] = None,
        roles: Optional[str] = None,
        ordering: Optional[str] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None
    ) -> dict[str, Any]:
        """
        List users with optional filters.

        Args:
            search: Search by username/email/name
            is_active: Filter by active status
            is_staff: Filter by staff status
            is_superuser: Filter by superuser status
            is_deleted: Filter by deleted status
            roles: Comma-separated role slugs (e.g., "admin,manager")
            ordering: Sort field (e.g., "-created_at")
            page: Page number
            page_size: Items per page

        Returns:
            dict: User list response with pagination

        Example:
            ```python
            users = await client.users.list_users(
                is_active=True,
                roles="admin",
                page=1,
                page_size=20
            )
            for user in users["results"]:
                print(user["username"])
            ```
        """
        path = _build_user_list_path(
            search, is_active, is_staff, is_superuser,
            is_deleted, roles, ordering, page, page_size
        )
        response = await self._http.get(path)
        return response

    async def get_user_apps(self, username: str) -> list[dict[str, Any]]:
        """
        Get apps associated with a user.

        Args:
            username: Username to get apps for

        Returns:
            list: List of apps

        Example:
            ```python
            apps = await client.users.get_user_apps("alice")
            for app in apps:
                print(app["slug"])
            ```
        """
        response = await self._http.get(f"/api/users/{username}/apps/")
        return _parse_user_apps(response)

    async def assign_roles(
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
            result = await client.users.assign_roles(
                roles=["admin", "manager"],
                usernames=["alice", "bob"],
                expires_at="2025-06-15T23:59:59Z"  # Optional
            )
            print(result["message"])  # "Assigned 4 roles successfully"

            # Permanent assignment (no expiration)
            result = await client.users.assign_roles(
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
        response = await self._http.post(path, json=body)
        return response

    async def revoke_roles(
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
            result = await client.users.revoke_roles(
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
        response = await self._http.request("DELETE", path, json=body)
        return response


