"""
App API Module

Provides methods for:
- App-level operations
- Role management
- App settings retrieval
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from taruvi.modules.base import BaseModule


if TYPE_CHECKING:
    from taruvi._async.client import AsyncClient

# API endpoint paths for app
_APP_ROLES = "/api/apps/{app_slug}/roles/"
_APP_SETTINGS = "/api/apps/{app_slug}/settings/"


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

    async def settings(self, app_slug: Optional[str] = None) -> dict[str, Any]:
        """
        Get app settings.

        Args:
            app_slug: App slug (defaults to client's app_slug)

        Returns:
            dict with app settings: display_name, primary_color, secondary_color,
            icon, icon_url, icon_background_color, category,
            documentation_url, support_email, default_frontend_worker_url,
            created_at, updated_at

        Example:
            ```python
            settings = await client.app.settings()
            print(settings['display_name'])
            print(settings['primary_color'])
            ```
        """
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _APP_SETTINGS.format(app_slug=app_slug)
        response = await self._http.get(path)
        return response
