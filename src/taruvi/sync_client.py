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
from taruvi.runtime import RuntimeMode, detect_runtime
from taruvi.sync_http_client import SyncHTTPClient
from taruvi.modules.sync_functions import SyncFunctionsModule
from taruvi.modules.sync_database import SyncDatabaseModule
from taruvi.modules.sync_auth import SyncAuthModule


class SyncClient:
    """
    Native Synchronous Taruvi API Client.

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
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        site_slug: Optional[str] = None,
        app_slug: Optional[str] = None,
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
            site_slug: Site slug for multi-tenant routing
            app_slug: App slug (optional)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            retry_backoff_factor: Backoff factor for retries
            debug: Enable debug logging
            verify_ssl: Verify SSL certificates
            pool_connections: Connection pool size
            pool_maxsize: Maximum pool size
            **kwargs: Additional configuration options
        """
        # Detect runtime mode and auto-configure if needed
        runtime_mode = detect_runtime()

        # Auto-configure from environment if no explicit config
        if runtime_mode == RuntimeMode.FUNCTION and not (api_url or api_key):
            runtime_config = self._load_config_from_runtime()
            api_url = runtime_config.get("api_url") or api_url
            api_key = runtime_config.get("api_key") or api_key
            site_slug = runtime_config.get("site_slug") or site_slug
            app_slug = runtime_config.get("app_slug") or app_slug

        # Build configuration
        self._config = TaruviConfig(
            api_url=api_url or "http://localhost:8000",
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
            **kwargs,
        )

        # Validate required fields
        self._config.validate_required_fields()

        # Create native blocking HTTP client (NO asyncio!)
        self._http = SyncHTTPClient(self._config)

        # Lazy-load modules
        self._functions = None
        self._database = None
        self._auth = None

    def _load_config_from_runtime(self) -> dict[str, Optional[str]]:
        """
        Load configuration from runtime environment variables.

        Returns:
            dict: Configuration values from environment
        """
        import os

        return {
            "api_url": os.getenv("TARUVI_API_URL"),
            "api_key": os.getenv("TARUVI_API_KEY"),
            "site_slug": os.getenv("TARUVI_SITE_SLUG"),
            "app_slug": os.getenv("TARUVI_APP_SLUG"),
        }

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

    def as_user(self, user_jwt: str) -> "SyncClient":
        """
        Create a new client with user context.

        Args:
            user_jwt: User's JWT token

        Returns:
            SyncClient: New client instance with user context

        Example:
            ```python
            user_client = service_client.as_user(user_jwt="user_token")
            result = user_client.database.query("orders").get()
            ```
        """
        return SyncClient(
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
            f"SyncClient(api_url={self._config.api_url!r}, "
            f"site_slug={self._config.site_slug!r})"
        )
