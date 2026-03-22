"""
Analytics API Module

Provides methods for:
- Executing analytics queries with parameters
- Getting query results
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from taruvi.modules.base import BaseModule

if TYPE_CHECKING:
    from taruvi._sync.client import SyncClient

# API endpoint paths for analytics
_ANALYTICS_EXECUTE = "/api/apps/{app_slug}/analytics/queries/{query_slug}/execute/"


class AnalyticsModule(BaseModule):
    """Analytics API operations."""

    def __init__(self, client: "SyncClient") -> None:
        """Initialize AnalyticsModule."""
        self.client = client
        super().__init__(client._http_client, client._config)

    def execute(
        self,
        query_slug: str,
        params: Optional[dict[str, Any]] = None,
        *,
        app_slug: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Execute an analytics query.

        Args:
            query_slug: Analytics query slug (e.g., "monthly-revenue")
            params: Query parameters (filters, date ranges, etc.)
            app_slug: App slug (defaults to client's app_slug)

        Returns:
            dict: Query results with 'data' key containing results

        Example:
            ```python
            # Execute analytics query
            result = client.analytics.execute(
                "monthly-revenue",
                params={
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31"
                }
            )
            print(result["data"])

            # Query with grouping
            result = client.analytics.execute(
                "user-signups",
                params={
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31",
                    "group_by": "month"
                }
            )

            # Query with filters
            result = client.analytics.execute(
                "sales-by-region",
                params={
                    "region": "US",
                    "product_category": "electronics"
                }
            )
            ```
        """
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _ANALYTICS_EXECUTE.format(
            app_slug=app_slug,
            query_slug=query_slug
        )

        body = {
            "params": params or {}
        }

        response = self._http.post(path, json=body)
        return self._extract_data(response)
