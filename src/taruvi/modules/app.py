"""
App API Module

Provides methods for:
- App-level operations
- Role management
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from taruvi.models.app import Role, RoleListResponse

if TYPE_CHECKING:
    from taruvi.client import Client
    from taruvi.sync_client import SyncClient

# API endpoint paths for app
_APP_ROLES = "/api/app/{app_slug}/roles"


# ============================================================================
# Async Implementation
# ============================================================================

class AppModule:
    """App API operations."""

    def __init__(self, client: "Client") -> None:
        """Initialize App module."""
        self.client = client
        self._http = client._http_client
        self._config = client._config

    async def roles(self, app_slug: Optional[str] = None) -> RoleListResponse:
        """
        Get app roles.

        Args:
            app_slug: App slug (defaults to client's app_slug)

        Returns:
            RoleListResponse: List of roles

        Example:
            ```python
            roles = await client.app.roles()
            for role in roles.data:
                print(f"{role.name}: {role.permissions}")
            ```
        """
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _APP_ROLES.format(app_slug=app_slug)
        response = await self._http.get(path)
        return RoleListResponse.from_dict(response)


# ============================================================================
# Sync Implementation
# ============================================================================

class SyncAppModule:
    """Synchronous App API operations."""

    def __init__(self, client: "SyncClient") -> None:
        """Initialize App module."""
        self.client = client
        self._http = client._http
        self._config = client._config

    def roles(self, app_slug: Optional[str] = None) -> RoleListResponse:
        """Get app roles (blocking)."""
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _APP_ROLES.format(app_slug=app_slug)
        response = self._http.get(path)
        return RoleListResponse.from_dict(response)
