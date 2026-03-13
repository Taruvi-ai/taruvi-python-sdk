"""
Settings API Module

Provides methods for:
- Retrieving site metadata and settings
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from taruvi.modules.base import BaseModule


if TYPE_CHECKING:
    from taruvi._async.client import AsyncClient

# API endpoint paths for settings
_SETTINGS_METADATA = "/api/settings/metadata/"
_USER_ATTRIBUTES = "/api/settings/user-attributes/"


class AsyncSettingsModule(BaseModule):
    """Settings API operations."""

    def __init__(self, client: "AsyncClient") -> None:
        """Initialize SettingsModule."""
        self.client = client
        super().__init__(client._http_client, client._config)

    async def get(self) -> dict[str, Any]:
        """
        Get site metadata and settings.

        Returns:
            SiteSettings: Site settings/metadata

        Example:
            ```python
            settings = await client.settings.get()
            print(settings.to_dict())
            ```
        """
        response = await self._http.get(_SETTINGS_METADATA)
        return response

    async def user_attributes(self) -> dict[str, Any]:
        """
        Get all user attributes defined in the site.

        Returns:
            dict: User attributes schema/list

        Example:
            ```python
            attributes = await client.settings.user_attributes()
            print(attributes)
            ```
        """
        response = await self._http.get(_USER_ATTRIBUTES)
        return response
