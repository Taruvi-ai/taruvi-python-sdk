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
        app_slug: str,
        *,
        # Configuration (project-level only)
        timeout: int = 30,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> None:
        """
        Initialize Taruvi sync client (project-level configuration).

        Authentication is handled separately via the auth property.

        Args:
            api_url: Taruvi API base URL
            app_slug: Application slug (required)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            **kwargs: Additional configuration options

        Example:
            >>> client = Client(
            ...     api_url='https://app.taruvi.com',
            ...     app_slug='my-app',
            ...     mode='sync'
            ... )
            >>> # Authenticate using auth module
            >>> auth_client = client.auth.signInWithToken(token='...', token_type='jwt')
        """
        # Use factory method - handles runtime detection and merging
        self._config = TaruviConfig.from_runtime_and_params(
            api_url=api_url,
            app_slug=app_slug,
            timeout=timeout,
            max_retries=max_retries,
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
    def auth(self):
        """
        Authentication manager for user-level auth operations.

        Returns:
            AuthManager instance for this client

        Example:
            >>> # Sign in with JWT
            >>> auth_client = client.auth.signInWithToken(token='jwt_token', token_type='jwt')

            >>> # Sign in with username/password
            >>> auth_client = client.auth.signInWithPassword(username='...', password='...')

            >>> # Refresh token
            >>> new_client = client.auth.refreshToken(refresh_token='...')

            >>> # Sign out
            >>> unauth_client = auth_client.auth.signOut()
        """
        if self._auth is None:
            from taruvi.auth import AuthManager
            self._auth = AuthManager(self)
        return self._auth

    @property
    def is_authenticated(self) -> bool:
        """
        Check if client has authentication credentials.

        Returns:
            True if client has jwt, api_key, or session_token configured

        Example:
            >>> client = Client(api_url='...', app_slug='...', mode='sync')
            >>> client.is_authenticated
            False
            >>> auth_client = client.auth.signInWithToken(token='...', token_type='jwt')
            >>> auth_client.is_authenticated
            True
        """
        return any([
            self._config.jwt is not None,
            self._config.api_key is not None,
            self._config.session_token is not None,
        ])

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
