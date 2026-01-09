"""
App API Module

Provides methods for:
- App-level operations
- Role management
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from taruvi.modules.base import BaseModule


if TYPE_CHECKING:
    from taruvi._async.client import AsyncClient

# API endpoint paths for app
_APP_ROLES = "/api/app/{app_slug}/roles"


class AsyncAppModule(BaseModule):
    """App API operations."""

    def __init__(self, client: "AsyncClient") -> None:
        """Initialize AppModule."""
        self.client = client
        super().__init__(client._http_client, client._config)

    async def roles(self, app_slug: Optional[str] = None) -> dict[str, Any]:
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
        return response
