"""
Secrets API Module

Provides methods for:
- Listing secrets with filters (search, app, tags, type, pagination)
- Getting specific secret values with 2-tier inheritance
- Batch getting multiple secrets efficiently (single request)
- Updating secret values
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from taruvi.modules.base import BaseModule
from taruvi.utils import build_params
from taruvi.types import Secret


if TYPE_CHECKING:
    from taruvi._async.client import AsyncClient

# API endpoint paths for secrets
_SECRETS_BASE = "/api/secrets/"
_SECRET_DETAIL = "/api/secrets/{key}/"


class AsyncSecretsModule(BaseModule):
    """Secrets API operations."""

    def __init__(self, client: "AsyncClient") -> None:
        """Initialize SecretsModule."""
        self.client = client
        super().__init__(client._http_client, client._config)

    async def list(
        self,
        keys: Optional[list[str]] = None,
        *,
        search: Optional[str] = None,
        app: Optional[str] = None,
        tags: Optional[list[str]] = None,
        secret_type: Optional[str] = None,
        include_metadata: bool = False,
        page: Optional[int] = None,
        page_size: Optional[int] = None
    ) -> dict[str, Any]:
        """
        List secrets with optional filters or batch-get by keys.

        Args:
            keys: Optional list of secret keys for batch retrieval
            search: Search by key (partial, case-insensitive)
            app: Filter by app context (defaults to client's app_slug if available)
            tags: Filter by tags (list of tag names)
            secret_type: Filter by type (e.g., "api_key", "database")
            include_metadata: If True, returns full secret objects for batch keys
            page: Page number for pagination
            page_size: Items per page (max 100)

        Returns:
            Full API response with status, message, data, and total:
            {
                "status": "success",
                "message": "Secrets retrieved successfully",
                "data": [...],
                "total": 50
            }

        Example:
            ```python
            # List all secrets
            result = await client.secrets.list_secrets()
            secrets = result["data"]
            total = result["total"]

            # List with filters
            result = await client.secrets.list_secrets(
                secret_type="api_key",
                tags=["production"],
                page_size=50
            )
            for secret in result["data"]:
                print(f"{secret['key']}: {secret['value'][:4]}...")

            # Batch get (values only)
            secrets_map = await client.secrets.list(
                keys=["API_KEY", "DB_PASSWORD"]
            )

            # Batch get with metadata
            secrets_meta = await client.secrets.list(
                keys=["API_KEY"],
                include_metadata=True
            )
            ```
        """
        # Auto-use client's app_slug if no app specified
        if app is None and self._config.app_slug:
            app = self._config.app_slug
        
        params = build_params(
            keys=",".join(keys) if keys else None,
            search=search,
            app=app,
            tags=",".join(tags) if tags else None,
            secret_type=secret_type,
            include_metadata=include_metadata,
            page=page,
            page_size=page_size,
        )
        response = await self._http.get(_SECRETS_BASE, params=params)
        return response

    async def get(
        self,
        key: str,
        *,
        app: Optional[str] = None,
        tags: Optional[list[str]] = None
    ) -> Secret:
        """
        Get a specific secret by key.

        Args:
            key: Secret key/name
            app: App context for 2-tier inheritance (defaults to client's app_slug if available)
            tags: Tag validation (returns 404 if secret doesn't have these tags)

        Returns:
            Secret dict with key, value, tags, secret_type, etc.

        Raises:
            NotFoundError: If secret doesn't exist

        Example:
            ```python
            # Simple get (uses client's app_slug if set)
            api_key = await client.secrets.get("API_KEY")
            print(f"API Key: {api_key['value']}")

            # Get with explicit app context (2-tier inheritance)
            db_pass = await client.secrets.get(
                "DB_PASSWORD",
                app="production"
            )

            # Get with tag validation
            stripe_key = await client.secrets.get(
                "STRIPE_KEY",
                tags=["payment", "production"]
            )
            ```
        """
        # Auto-use client's app_slug if no app specified
        if app is None and self._config.app_slug:
            app = self._config.app_slug
        
        path = _SECRET_DETAIL.format(key=key)

        params = build_params(
            app=app,
            tags=",".join(tags) if tags else None,
        )

        response = await self._http.get(path, params=params)
        return self._extract_data(response)

    # get_many removed: use list(keys=[...]) instead
