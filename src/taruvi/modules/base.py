"""
Base Module Class with Shared Utilities

Provides common functionality for all Taruvi modules:
- Initialization
- App slug validation
- Response data extraction
- Common patterns
"""

from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from taruvi.config import TaruviConfig
    from taruvi.http_client import HTTPClient
    from taruvi.sync_http_client import SyncHTTPClient


class BaseModule:
    """
    Base class for all Taruvi API modules.

    Provides shared utilities and common patterns to eliminate code duplication.

    Features:
    - Centralized app_slug validation
    - Response data extraction helpers
    - HTTP client access
    - Configuration access
    """

    def __init__(
        self,
        http_client: Union["HTTPClient", "SyncHTTPClient"],
        config: "TaruviConfig",
    ) -> None:
        """
        Initialize base module.

        Args:
            http_client: HTTP client (async or sync)
            config: Taruvi configuration
        """
        self._http = http_client
        self._config = config

    def _ensure_app_slug(self, app_slug: Optional[str] = None) -> str:
        """
        Validate and return app_slug.

        Uses provided app_slug or falls back to config.app_slug.
        Raises ValueError if neither is available.

        Args:
            app_slug: Optional app slug override

        Returns:
            Valid app slug

        Raises:
            ValueError: If app_slug is not provided and not in config

        Example:
            app_slug = self._ensure_app_slug(custom_app_slug)
        """
        result = app_slug or self._config.app_slug
        if not result:
            raise ValueError(
                "app_slug is required. Provide it as a parameter or set it in the client configuration."
            )
        return result

    @staticmethod
    def _extract_data(response: dict[str, Any], default: Any = None) -> Any:
        """
        Extract 'data' field from API response.

        Most Taruvi API responses follow the format: {"data": {...}, "meta": {...}}
        This helper extracts the data field with a default fallback.

        Args:
            response: API response dict
            default: Default value if 'data' key not found (default: {})

        Returns:
            Extracted data or default value

        Example:
            data = self._extract_data(response)
            # Returns response["data"] or {}

            data = self._extract_data(response, default=[])
            # Returns response["data"] or []
        """
        if default is None:
            default = {}
        return response.get("data", default)

    @staticmethod
    def _extract_data_list(response: dict[str, Any]) -> list[Any]:
        """
        Extract 'data' field from API response, expecting a list.

        Convenience method for responses that return lists.

        Args:
            response: API response dict

        Returns:
            Extracted data as list (empty list if not found)

        Example:
            items = self._extract_data_list(response)
            # Returns response["data"] or []
        """
        return response.get("data", [])

    @staticmethod
    def _extract_count(response: dict[str, Any]) -> int:
        """
        Extract 'count' field from paginated API response.

        Args:
            response: API response dict

        Returns:
            Count value or 0 if not found

        Example:
            total = self._extract_count(response)
            # Returns response["count"] or 0
        """
        return response.get("count", 0)

    @staticmethod
    def _extract_results(response: dict[str, Any]) -> list[Any]:
        """
        Extract 'results' field from paginated API response.

        Args:
            response: API response dict

        Returns:
            Results list or empty list if not found

        Example:
            items = self._extract_results(response)
            # Returns response["results"] or []
        """
        return response.get("results", [])

    def _build_list_params(
        self,
        page: int = 1,
        page_size: Optional[int] = None,
        **extra_filters: Any,
    ) -> dict[str, Any]:
        """
        Build standard pagination params.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            **extra_filters: Additional query parameters

        Returns:
            Query parameters dict

        Example:
            params = self._build_list_params(
                page=2,
                page_size=50,
                status="active",
                search="query"
            )
            # Returns: {"page": 2, "page_size": 50, "status": "active", "search": "query"}
        """
        params: dict[str, Any] = {}

        if page != 1:
            params["page"] = page

        if page_size is not None:
            params["page_size"] = page_size

        # Add any extra filters
        params.update(extra_filters)

        return params
