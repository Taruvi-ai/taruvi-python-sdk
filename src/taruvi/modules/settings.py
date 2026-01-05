"""
Settings API Module

Provides methods for:
- Retrieving site metadata and settings
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from taruvi.client import Client
    from taruvi.sync_client import SyncClient

# API endpoint paths for settings
_SETTINGS_METADATA = "/api/settings/metadata/"


class SettingsModule:
    """Settings API operations."""

    def __init__(self, client: "Client") -> None:
        """
        Initialize Settings module.

        Args:
            client: Taruvi client instance
        """
        self.client = client
        self._http = client._http_client
        self._config = client._config

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


class SyncSettingsModule:
    """Synchronous Settings API operations."""

    def __init__(self, client: "SyncClient") -> None:
        """
        Initialize Settings module.

        Args:
            client: Taruvi sync client instance
        """
        self.client = client
        self._http = client._http
        self._config = client._config

    def get(self) -> dict[str, Any]:
        """
        Get site metadata and settings (blocking).

        Returns:
            SiteSettings: Site settings/metadata
        """
        response = self._http.get(_SETTINGS_METADATA)
        return response
