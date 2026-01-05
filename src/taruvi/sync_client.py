"""
Native Synchronous Taruvi Client

Uses httpx.Client (blocking) - NO asyncio.run() wrapper.
Thread-safe and works in all Python environments including
Jupyter notebooks, FastAPI apps, and async contexts.

Provides synchronous interface for:
- Function execution
- Database operations
- Authentication
"""

from typing import Any, Optional

from taruvi.config import TaruviConfig
from taruvi.sync_http_client import SyncHTTPClient
from taruvi.modules.functions import SyncFunctionsModule
from taruvi.modules.database import SyncDatabaseModule
from taruvi.modules.auth import SyncAuthModule


class _SyncClient:
    """
    Internal synchronous Taruvi API client implementation.

    Note: This is an internal class. Users should use the `Client()` factory function instead.

    Uses httpx.Client (blocking) - NO asyncio.run() wrapper.
    Thread-safe and works in any Python environment.

    **Performance**: 10-50x faster than asyncio wrapper pattern for high-frequency usage.

    **Compatibility**: Works in Jupyter notebooks, FastAPI apps, and any async context.

    External Application Mode:
        ```python
        client = SyncClient(
            api_url="http://localhost:8000",
            api_key="your_jwt_token",
            site_slug="your-site"
        )

        result = client.functions.execute("my-function", {"param": "value"})
        ```

    Function Runtime Mode (auto-configured):
        ```python
        # Inside Taruvi function - no configuration needed!
        def main(params, user_data):
            from taruvi import SyncClient

            client = SyncClient()
            result = client.functions.execute("other-function", {"data": 123})
            return result["data"]
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
        verify_ssl: bool = True,
        pool_connections: int = 10,
        pool_maxsize: int = 10,
        **kwargs: Any,
    ) -> None:
        """
        Initialize native synchronous Taruvi client.

        Args:
            api_url: Taruvi API base URL
            api_key: JWT token for authentication
            app_slug: Application slug (required)
            site_slug: Site slug for multi-tenant routing
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            retry_backoff_factor: Backoff factor for retries
            debug: Enable debug logging
            verify_ssl: Verify SSL certificates
            pool_connections: Connection pool size
            pool_maxsize: Maximum pool size
            **kwargs: Additional configuration options
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
            verify_ssl=verify_ssl,
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
            **kwargs
        )

        # Validate required fields
        self._config.validate_required_fields()

        # Create native blocking HTTP client (NO asyncio!)
        self._http = SyncHTTPClient(self._config)

        # Lazy-load modules
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
    def functions(self) -> SyncFunctionsModule:
        """
        Access Functions API (native blocking).

        Returns:
            SyncFunctionsModule: Functions API module
        """
        if self._functions is None:
            self._functions = SyncFunctionsModule(self)
        return self._functions

    @property
    def database(self) -> SyncDatabaseModule:
        """
        Access Database API (native blocking).

        Returns:
            SyncDatabaseModule: Database API module
        """
        if self._database is None:
            self._database = SyncDatabaseModule(self)
        return self._database

    @property
    def auth(self) -> SyncAuthModule:
        """
        Access Auth API (native blocking).

        Returns:
            SyncAuthModule: Auth API module
        """
        if self._auth is None:
            self._auth = SyncAuthModule(self)
        return self._auth

    @property
    def storage(self):
        """Access Storage API (native blocking)."""
        if self._storage is None:
            from taruvi.modules.storage import SyncStorageModule
            self._storage = SyncStorageModule(self)
        return self._storage

    @property
    def secrets(self):
        """Access Secrets API (native blocking)."""
        if self._secrets is None:
            from taruvi.modules.secrets import SyncSecretsModule
            self._secrets = SyncSecretsModule(self)
        return self._secrets

    @property
    def policy(self):
        """Access Policy API (native blocking)."""
        if self._policy is None:
            from taruvi.modules.policy import SyncPolicyModule
            self._policy = SyncPolicyModule(self)
        return self._policy

    @property
    def app(self):
        """Access App API (native blocking)."""
        if self._app is None:
            from taruvi.modules.app import SyncAppModule
            self._app = SyncAppModule(self)
        return self._app

    @property
    def settings(self):
        """Access Settings API (native blocking)."""
        if self._settings is None:
            from taruvi.modules.settings import SyncSettingsModule
            self._settings = SyncSettingsModule(self)
        return self._settings

    def as_user(self, user_jwt: str) -> "_SyncClient":
        """
        Create a new client with user context.

        Args:
            user_jwt: User's JWT token

        Returns:
            _SyncClient: New client instance with user context

        Example:
            ```python
            user_client = service_client.as_user(user_jwt="user_token")
            result = user_client.database.query("orders").get()
            ```
        """
        return _SyncClient(
            api_url=self._config.api_url,
            api_key=user_jwt,
            site_slug=self._config.site_slug,
            app_slug=self._config.app_slug,
            timeout=self._config.timeout,
            max_retries=self._config.max_retries,
            retry_backoff_factor=self._config.retry_backoff_factor,
            debug=self._config.debug,
            verify_ssl=self._config.verify_ssl,
            pool_connections=self._config.pool_connections,
            pool_maxsize=self._config.pool_maxsize,
            user_jwt=user_jwt,
        )

    def close(self) -> None:
        """Close the HTTP client and release resources."""
        self._http.close()

    def __enter__(self):
        """Support context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close client on context exit."""
        self.close()

    def __repr__(self) -> str:
        """String representation of client."""
        return (
            f"_SyncClient(api_url={self._config.api_url!r}, "
            f"site_slug={self._config.site_slug!r})"
        )
