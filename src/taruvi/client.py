"""
Taruvi SDK Client

Main client class for interacting with Taruvi API.
Supports both external application mode and function runtime mode.
"""

from typing import Any, Optional, Union, Literal, overload

from taruvi.config import TaruviConfig
from taruvi.http_client import HTTPClient


class _AsyncClient:
    """
    Internal async Taruvi API client implementation.

    Note: This is an internal class. Users should use the `Client()` factory function instead.

    This client automatically detects whether it's running in an external application
    or inside a Taruvi function and configures itself accordingly.

    External Application Mode:
        ```python
        client = Client(
            api_url="http://localhost:8000",
            api_key="your_jwt_token",
            site_slug="your-site"
        )

        result = await client.functions.execute("my-function", {"param": "value"})
        ```

    Function Runtime Mode (auto-configured):
        ```python
        # No configuration needed - auto-detects from environment!
        client = Client()

        result = await client.functions.execute("other-function", {"data": 123})
        ```
    """

    def __init__(
        self,
        api_url: str,
        api_key: str,
        app_slug: str,
        *,
        site_slug: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        retry_backoff_factor: float = 0.5,
        debug: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Initialize Taruvi async client.

        Args:
            api_url: Taruvi API base URL (e.g., "http://localhost:8000")
            api_key: JWT token for authentication
            app_slug: Application slug (required)
            site_slug: Site slug for multi-tenant routing
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            retry_backoff_factor: Backoff factor for retries
            debug: Enable debug logging
            **kwargs: Additional configuration options

        Raises:
            ConfigurationError: If required configuration is missing
        """
        # Use factory method - handles runtime detection and merging
        self._config = TaruviConfig.from_runtime_and_params(
            api_url=api_url,
            api_key=api_key,
            site_slug=site_slug,
            app_slug=app_slug,
            timeout=timeout,
            max_retries=max_retries,
            retry_backoff_factor=retry_backoff_factor,
            debug=debug,
            **kwargs
        )

        # Validate configuration
        self._config.validate_required_fields()

        # Create HTTP client
        self._http_client = HTTPClient(self._config)

        # Module instances (lazy-loaded)
        self._functions = None
        self._database = None
        self._auth = None
        self._storage = None
        self._secrets = None
        self._policy = None
        self._app = None
        self._settings = None

    @property
    def config(self) -> TaruviConfig:
        """Get client configuration."""
        return self._config

    @property
    def functions(self):
        """Access Functions API."""
        if self._functions is None:
            from taruvi.modules.functions import FunctionsModule

            self._functions = FunctionsModule(self)
        return self._functions

    @property
    def database(self):
        """Access Database API."""
        if self._database is None:
            from taruvi.modules.database import DatabaseModule

            self._database = DatabaseModule(self)
        return self._database

    @property
    def auth(self):
        """Access Auth API."""
        if self._auth is None:
            from taruvi.modules.auth import AuthModule

            self._auth = AuthModule(self)
        return self._auth

    @property
    def storage(self):
        """Access Storage API."""
        if self._storage is None:
            from taruvi.modules.storage import StorageModule

            self._storage = StorageModule(self)
        return self._storage

    @property
    def secrets(self):
        """Access Secrets API."""
        if self._secrets is None:
            from taruvi.modules.secrets import SecretsModule

            self._secrets = SecretsModule(self)
        return self._secrets

    @property
    def policy(self):
        """Access Policy API."""
        if self._policy is None:
            from taruvi.modules.policy import PolicyModule

            self._policy = PolicyModule(self)
        return self._policy

    @property
    def app(self):
        """Access App API."""
        if self._app is None:
            from taruvi.modules.app import AppModule

            self._app = AppModule(self)
        return self._app

    @property
    def settings(self):
        """Access Settings API."""
        if self._settings is None:
            from taruvi.modules.settings import SettingsModule

            self._settings = SettingsModule(self)
        return self._settings

    def as_user(self, user_jwt: str) -> "_AsyncClient":
        """
        Create a new client with user context (for permission-aware operations).

        This allows making API calls with a specific user's permissions,
        useful for service accounts that need to act on behalf of users.

        Args:
            user_jwt: User's JWT token

        Returns:
            _AsyncClient: New client instance with user context

        Example:
            ```python
            # Service client (admin permissions)
            service_client = Client(mode='async', api_key="service_key", ...)

            # User-scoped client
            user_client = service_client.as_user(user_jwt="user_token")

            # This call respects user's permissions
            result = await user_client.database.query("orders").get()
            ```
        """
        return _AsyncClient(
            api_url=self._config.api_url,
            api_key=user_jwt,  # Use user JWT as api_key
            site_slug=self._config.site_slug,
            app_slug=self._config.app_slug,
            timeout=self._config.timeout,
            max_retries=self._config.max_retries,
            retry_backoff_factor=self._config.retry_backoff_factor,
            debug=self._config.debug,
            user_jwt=user_jwt,
        )

    async def close(self) -> None:
        """Close the client and release resources."""
        await self._http_client.close()

    async def __aenter__(self):
        """Support async context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close client on context exit."""
        await self.close()

    def __repr__(self) -> str:
        """String representation of client."""
        mode = self._config.runtime_mode.value
        return (
            f"_AsyncClient(api_url={self._config.api_url}, "
            f"site_slug={self._config.site_slug}, "
            f"mode={mode})"
        )


# Unified Client Factory Function
# ============================================================

@overload
def Client(
    api_url: str,
    api_key: str,
    site_slug: str,
    app_slug: str,
    mode: Literal['async'],
    *,
    timeout: int = 30,
    max_retries: int = 3,
    retry_backoff_factor: float = 0.5,
    debug: bool = False,
    **kwargs: Any,
) -> _AsyncClient: ...


@overload
def Client(
    api_url: str,
    api_key: str,
    site_slug: str,
    app_slug: str,
    mode: Literal['sync'] = 'sync',
    *,
    timeout: int = 30,
    max_retries: int = 3,
    retry_backoff_factor: float = 0.5,
    debug: bool = False,
    verify_ssl: bool = True,
    pool_connections: int = 10,
    pool_maxsize: int = 10,
    **kwargs: Any,
) -> "_SyncClient": ...


def Client(
    api_url: str,
    api_key: str,
    site_slug: str,
    app_slug: str,
    mode: str = 'sync',
    **config: Any
) -> Union[_AsyncClient, "_SyncClient"]:
    """
    Create a Taruvi client.

    Args:
        api_url: Taruvi API base URL
        api_key: API authentication key
        site_slug: Site identifier (required)
        app_slug: Application slug (required)
        mode: Client mode - 'sync' (default) or 'async'
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
        retry_backoff_factor: Backoff factor for retries
        debug: Enable debug logging
        verify_ssl: Verify SSL certificates (sync mode only)
        pool_connections: Connection pool size (sync mode only)
        pool_maxsize: Max pool size (sync mode only)
        **config: Additional configuration options

    Returns:
        Configured client instance (_AsyncClient or _SyncClient)

    Examples:
        # Sync mode (default)
        client = Client("https://api.taruvi.com", "key", "my-site", "my-app")
        result = client.functions.execute("my-function", params={})

        # Async mode
        client = Client("https://api.taruvi.com", "key", "my-site", "my-app", "async")
        result = await client.functions.execute("my-function", params={})

    Raises:
        ValueError: If mode is not 'sync' or 'async'
    """
    if mode == 'async':
        # Remove sync-only parameters if present
        config.pop('verify_ssl', None)
        config.pop('pool_connections', None)
        config.pop('pool_maxsize', None)
        return _AsyncClient(api_url, api_key, app_slug, site_slug=site_slug, **config)
    elif mode == 'sync':
        from taruvi.sync_client import _SyncClient
        return _SyncClient(api_url, api_key, app_slug, site_slug=site_slug, **config)
    else:
        raise ValueError(
            f"Invalid mode: '{mode}'. Must be 'sync' or 'async'. "
            f"Use Client(mode='sync') for synchronous or Client(mode='async') for async/await."
        )
