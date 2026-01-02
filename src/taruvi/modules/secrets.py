"""
Secrets API Module

Provides methods for:
- Listing secrets
- Getting specific secret values
- Updating secret values
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from taruvi.models.secrets import Secret, SecretListResponse

if TYPE_CHECKING:
    from taruvi.client import Client
    from taruvi.sync_client import SyncClient

# API endpoint paths for secrets
_SECRETS_BASE = "/api/secrets/"
_SECRET_DETAIL = "/api/secrets/{key}/"


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

    async def list(self) -> SecretListResponse:
        """
        List all secrets.

        Returns:
            SecretListResponse: List of secrets

        Example:
            ```python
            secrets = await client.secrets.list()
            for secret in secrets.data:
                print(f"{secret.key}: {secret.value[:4]}...")
            ```
        """
        response = await self._http.get(_SECRETS_BASE)
        return SecretListResponse.from_dict(response)

    async def get(self, key: str) -> Secret:
        """
        Get a specific secret by key.

        Args:
            key: Secret key/name

        Returns:
            Secret: Secret object with value

        Raises:
            NotFoundError: If secret doesn't exist

        Example:
            ```python
            api_key = await client.secrets.get("API_KEY")
            print(f"API Key: {api_key.value}")
            ```
        """
        path = _SECRET_DETAIL.format(key=key)
        response = await self._http.get(path)
        return Secret.from_dict(response)

    async def update(self, key: str, value: str) -> Secret:
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
        return Secret.from_dict(response)


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

    def list(self) -> SecretListResponse:
        """List all secrets (blocking)."""
        response = self._http.get(_SECRETS_BASE)
        return SecretListResponse.from_dict(response)

    def get(self, key: str) -> Secret:
        """Get a specific secret by key (blocking)."""
        path = _SECRET_DETAIL.format(key=key)
        response = self._http.get(path)
        return Secret.from_dict(response)

    def update(self, key: str, value: str) -> Secret:
        """Update a secret's value (blocking)."""
        path = _SECRET_DETAIL.format(key=key)
        response = self._http.put(path, json={"value": value})
        return Secret.from_dict(response)
