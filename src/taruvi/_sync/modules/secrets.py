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

from taruvi.modules.base import BaseModule


if TYPE_CHECKING:
    from taruvi._sync.client import SyncClient

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


class SecretsModule(BaseModule):
    """Secrets API operations."""

    def __init__(self, client: "SyncClient") -> None:
        """Initialize SecretsModule."""
        self.client = client
        super().__init__(client._http_client, client._config)

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
        response = self._http.get(_SECRETS_BASE, params=params)
        return self._extract_data(response)

    def get_secret(
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

        response = self._http.get(path, params=params)
        return self._extract_data(response)

    def get_secrets(
        self,
        keys: list[str],
        *,
        app: Optional[str] = None,
        include_metadata: bool = False
    ) -> dict[str, Any]:
        """
        Get multiple secrets by keys using backend batch endpoint.

        More efficient than making multiple individual requests - uses a single API call.

        Args:
            keys: List of secret keys to retrieve
            app: Optional app context for 2-tier inheritance
            include_metadata: If True, returns full secret objects with tags and type

        Returns:
            Dict mapping keys to values (or full objects if include_metadata=True):

            Without metadata:
            {
                "API_KEY": "secret_value_123",
                "DB_PASSWORD": "db_pass_456"
            }

            With metadata:
            {
                "API_KEY": {
                    "value": "secret_value_123",
                    "tags": ["production"],
                    "secret_type": "api_credentials"
                }
            }

            Keys not found are omitted from results.

        Example:
            ```python
            # Get multiple secrets (values only)
            secrets = await client.secrets.get_secrets(
                ["API_KEY", "DB_PASSWORD", "STRIPE_KEY"]
            )
            api_key = secrets["API_KEY"]
            db_pass = secrets["DB_PASSWORD"]

            # Get with app context (2-tier inheritance)
            prod_secrets = await client.secrets.get_secrets(
                ["API_KEY", "DB_PASSWORD"],
                app="production"
            )

            # Get with metadata
            secrets_meta = await client.secrets.get_secrets(
                ["API_KEY"],
                include_metadata=True
            )
            api_key_value = secrets_meta["API_KEY"]["value"]
            api_key_tags = secrets_meta["API_KEY"]["tags"]
            ```
        """
        # Build request payload
        payload = {
            "keys": keys,
            "include_metadata": include_metadata
        }
        if app:
            payload["app"] = app

        # Make single batch API call
        response = self._http.post("/api/secrets/batch/", json=payload)
        return self._extract_data(response)

    def update(self, key: str, value: str) -> dict[str, Any]:
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
        response = self._http.put(path, json={"value": value})
        return response
