"""
Secrets API Module

Provides methods for:
- Listing secrets with filters (search, app, tags, type, pagination)
- Getting specific secret values with 2-tier inheritance
- Batch getting multiple secrets concurrently
- Updating secret values
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional


if TYPE_CHECKING:
    from taruvi.client import Client
    from taruvi.sync_client import SyncClient

# API endpoint paths for secrets
_SECRETS_BASE = "/api/secrets/"
_SECRET_DETAIL = "/api/secrets/{key}/"


# ============================================================================
# Helper Functions
# ============================================================================

def _build_list_params(
    search: Optional[str],
    app: Optional[str],
    tags: Optional[list[str]],
    secret_type: Optional[str],
    page: Optional[int],
    page_size: Optional[int]
) -> dict[str, Any]:
    """Build query parameters for list_secrets()."""
    params: dict[str, Any] = {}
    if search:
        params["search"] = search
    if app:
        params["app"] = app
    if tags:
        params["tags"] = ",".join(tags)
    if secret_type:
        params["secret_type"] = secret_type
    if page is not None:
        params["page"] = page
    if page_size is not None:
        params["page_size"] = page_size
    return params


# ============================================================================
# Async Implementation
# ============================================================================

class SecretsModule:
    """Secrets API operations."""

    def __init__(self, client: "Client") -> None:
        """Initialize Secrets module."""
        self.client = client
        self._http = client._http_client
        self._config = client._config

    async def list_secrets(
        self,
        *,
        search: Optional[str] = None,
        app: Optional[str] = None,
        tags: Optional[list[str]] = None,
        secret_type: Optional[str] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None
    ) -> dict[str, Any]:
        """
        List secrets with optional filters.

        Args:
            search: Search by key (partial, case-insensitive)
            app: Filter by app context
            tags: Filter by tags (list of tag names)
            secret_type: Filter by type (e.g., "api_key", "database")
            page: Page number for pagination
            page_size: Items per page (max 100)

        Returns:
            Paginated secret results with count, next, previous, results

        Example:
            ```python
            # List all secrets
            all_secrets = await client.secrets.list_secrets()

            # List with filters
            api_secrets = await client.secrets.list_secrets(
                secret_type="api_key",
                tags=["production"],
                page_size=50
            )
            for secret in api_secrets["results"]:
                print(f"{secret['key']}: {secret['value'][:4]}...")
            ```
        """
        params = _build_list_params(search, app, tags, secret_type, page, page_size)
        response = await self._http.get(_SECRETS_BASE, params=params)
        return response.get("data", {})

    async def get_secret(
        self,
        key: str,
        *,
        app: Optional[str] = None,
        tags: Optional[list[str]] = None
    ) -> dict[str, Any]:
        """
        Get a specific secret by key.

        Args:
            key: Secret key/name
            app: App context for 2-tier inheritance (checks app-level first, then site-level)
            tags: Tag validation (returns 404 if secret doesn't have these tags)

        Returns:
            Secret object with key, value, tags, secret_type, etc.

        Raises:
            NotFoundError: If secret doesn't exist

        Example:
            ```python
            # Simple get
            api_key = await client.secrets.get_secret("API_KEY")
            print(f"API Key: {api_key['value']}")

            # Get with app context (2-tier inheritance)
            db_pass = await client.secrets.get_secret(
                "DB_PASSWORD",
                app="production"
            )

            # Get with tag validation
            stripe_key = await client.secrets.get_secret(
                "STRIPE_KEY",
                tags=["payment", "production"]
            )
            ```
        """
        path = _SECRET_DETAIL.format(key=key)

        params = {}
        if app:
            params["app"] = app
        if tags:
            params["tags"] = ",".join(tags)

        response = await self._http.get(path, params=params)
        return response.get("data", {})

    async def get_secrets(
        self,
        keys: list[str],
        *,
        app: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Get multiple secrets by keys (client-side batching).

        Makes concurrent API calls internally for performance.

        Args:
            keys: List of secret keys to retrieve
            app: Optional app context for 2-tier inheritance

        Returns:
            Dict mapping keys to secret objects:
            {
                "API_KEY": {"key": "API_KEY", "value": "...", ...},
                "DB_PASSWORD": {"key": "DB_PASSWORD", "value": "...", ...}
            }

            Keys not found are omitted from results.

        Example:
            ```python
            # Get multiple secrets
            secrets = await client.secrets.get_secrets(
                ["API_KEY", "DB_PASSWORD", "STRIPE_KEY"]
            )
            api_key = secrets["API_KEY"]["value"]
            db_pass = secrets["DB_PASSWORD"]["value"]

            # Get with app context
            prod_secrets = await client.secrets.get_secrets(
                ["API_KEY", "DB_PASSWORD"],
                app="production"
            )
            ```
        """
        import asyncio

        params = {}
        if app:
            params["app"] = app

        async def fetch_one(key: str) -> tuple[str, Optional[dict]]:
            try:
                path = _SECRET_DETAIL.format(key=key)
                response = await self._http.get(path, params=params)
                return (key, response.get("data"))
            except Exception:
                return (key, None)

        # Fetch all concurrently
        results = await asyncio.gather(*[fetch_one(key) for key in keys])

        # Return dict excluding None values
        return {key: value for key, value in results if value is not None}

    async def update(self, key: str, value: str) -> dict[str, Any]:
        """
        Update a secret's value.

        Args:
            key: Secret key/name
            value: New secret value

        Returns:
            Secret: Updated secret object

        Example:
            ```python
            updated = await client.secrets.update(
                "API_KEY",
                "new_secret_value_123"
            )
            print(f"Updated: {updated.key}")
            ```
        """
        path = _SECRET_DETAIL.format(key=key)
        response = await self._http.put(path, json={"value": value})
        return response


# ============================================================================
# Sync Implementation
# ============================================================================

class SyncSecretsModule:
    """Synchronous Secrets API operations."""

    def __init__(self, client: "SyncClient") -> None:
        """Initialize Secrets module."""
        self.client = client
        self._http = client._http
        self._config = client._config

    def list_secrets(
        self,
        *,
        search: Optional[str] = None,
        app: Optional[str] = None,
        tags: Optional[list[str]] = None,
        secret_type: Optional[str] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None
    ) -> dict[str, Any]:
        """List secrets with optional filters (blocking)."""
        params = _build_list_params(search, app, tags, secret_type, page, page_size)
        response = self._http.get(_SECRETS_BASE, params=params)
        return response.get("data", {})

    def get_secret(
        self,
        key: str,
        *,
        app: Optional[str] = None,
        tags: Optional[list[str]] = None
    ) -> dict[str, Any]:
        """Get a specific secret by key (blocking)."""
        path = _SECRET_DETAIL.format(key=key)

        params = {}
        if app:
            params["app"] = app
        if tags:
            params["tags"] = ",".join(tags)

        response = self._http.get(path, params=params)
        return response.get("data", {})

    def get_secrets(
        self,
        keys: list[str],
        *,
        app: Optional[str] = None
    ) -> dict[str, Any]:
        """Get multiple secrets by keys (blocking, sequential)."""
        params = {}
        if app:
            params["app"] = app

        results = {}
        for key in keys:
            try:
                path = _SECRET_DETAIL.format(key=key)
                response = self._http.get(path, params=params)
                data = response.get("data")
                if data:
                    results[key] = data
            except Exception:
                continue
        return results

    def update(self, key: str, value: str) -> dict[str, Any]:
        """Update a secret's value (blocking)."""
        path = _SECRET_DETAIL.format(key=key)
        response = self._http.put(path, json={"value": value})
        return response
