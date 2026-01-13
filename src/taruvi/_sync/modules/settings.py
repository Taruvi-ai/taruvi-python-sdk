"""
Settings API Module

Provides methods for:
- Retrieving site metadata and settings
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from taruvi.modules.base import BaseModule


if TYPE_CHECKING:
    from taruvi._sync.client import SyncClient

# API endpoint paths for settings
_SETTINGS_METADATA = "/api/settings/metadata/"


class SettingsModule(BaseModule):
    """Settings API operations."""

    def __init__(self, client: "SyncClient") -> None:
        """Initialize SettingsModule."""
        self.client = client
        super().__init__(client._http_client, client._config)

    def get(self) -> dict[str, Any]:
        """
        Get site metadata and settings.

        Returns:
            SiteSettings: Site settings/metadata

        Example:
            ```python
            settings = client.settings.get()
            print(settings.to_dict())
            ```
        """
        response = self._http.get(_SETTINGS_METADATA)
        return response
