"""
Taruvi SDK Async Client

Async client class for interacting with Taruvi API.
Supports both external application mode and function runtime mode.
"""

from typing import Any

from taruvi.config import TaruviConfig
from taruvi._sync.http_client import HTTPClient


class SyncClient:
    """
    Async Taruvi API client implementation.

    This client automatically detects whether it's running in an external application
    or inside a Taruvi function and configures itself accordingly.

    External Application Mode:
        ```python
        client = Client(
            api_url="http://localhost:8000",
            api_key="your_jwt_token",
            site_slug="your-site",
            mode="async"
        )

        result = client.functions.execute("my-function", {"param": "value"})
        ```

    Function Runtime Mode (auto-configured):
        ```python
        # No configuration needed - auto-detects from environment!
        client = Client(mode="async")

        result = client.functions.execute("other-function", {"data": 123})
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
        Initialize Taruvi async client (project-level configuration).

        Authentication is handled separately via the auth property.

        Args:
            api_url: Taruvi API base URL (e.g., "http://localhost:8000")
            app_slug: Application slug (required)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            **kwargs: Additional configuration options

        Example:
            >>> client = Client(
            ...     api_url='https://app.taruvi.com',
            ...     app_slug='my-app',
            ...     mode='async'
            ... )
            >>> # Authenticate using auth module
            >>> auth_client = client.auth.signInWithToken(token='...', token_type='jwt')

        Raises:
            ConfigurationError: If required configuration is missing
        """
        # Use factory method - handles runtime detection and merging
        self._config = TaruviConfig.from_runtime_and_params(
            api_url=api_url,
            app_slug=app_slug,
            timeout=timeout,
            max_retries=max_retries,
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
        self._users = None
        self._analytics = None

    @property
    def config(self) -> TaruviConfig:
        """Get client configuration."""
        return self._config

    @property
    def functions(self):
        """Access Functions API."""
        if self._functions is None:
            from taruvi._sync.modules.functions import FunctionsModule

            self._functions = FunctionsModule(self)
        return self._functions

    @property
    def database(self):
        """Access Database API."""
        if self._database is None:
            from taruvi._sync.modules.database import DatabaseModule

            self._database = DatabaseModule(self)
        return self._database

    @property
    def auth(self):
        """
        Authentication module for user-level auth operations.

        Returns:
            AsyncAuthModule instance for this client

        Example:
            >>> # Sign in with JWT
            >>> auth_client = client.auth.signInWithToken(token='jwt_token', token_type='jwt')

            >>> # Sign in with username/password
            >>> auth_client = client.auth.signInWithPassword(username='...', password='...')

            >>> # Refresh token
            >>> new_client = client.auth.refreshToken(refresh_token='...')

            >>> # Sign out
            >>> unauth_client = auth_client.auth.signOut()

            >>> # Low-level API calls
            >>> response = client.auth.login(username='...', password='...')
            >>> user = client.auth.get_current_user()
        """
        if self._auth is None:
            from taruvi._sync.modules.auth import AuthModule
            self._auth = AuthModule(self)
        return self._auth

    @property
    def is_authenticated(self) -> bool:
        """
        Check if client has authentication credentials.

        Returns:
            True if client has jwt, api_key, or session_token configured

        Example:
            >>> client = Client(api_url='...', app_slug='...', mode='async')
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
        """Access Storage API."""
        if self._storage is None:
            from taruvi._sync.modules.storage import StorageModule

            self._storage = StorageModule(self)
        return self._storage

    @property
    def secrets(self):
        """Access Secrets API."""
        if self._secrets is None:
            from taruvi._sync.modules.secrets import SecretsModule

            self._secrets = SecretsModule(self)
        return self._secrets

    @property
    def policy(self):
        """Access Policy API."""
        if self._policy is None:
            from taruvi._sync.modules.policy import PolicyModule

            self._policy = PolicyModule(self)
        return self._policy

    @property
    def app(self):
        """Access App API."""
        if self._app is None:
            from taruvi._sync.modules.app import AppModule

            self._app = AppModule(self)
        return self._app

    @property
    def settings(self):
        """Access Settings API."""
        if self._settings is None:
            from taruvi._sync.modules.settings import SettingsModule

            self._settings = SettingsModule(self)
        return self._settings

    @property
    def users(self):
        """Access Users API for user and role management operations."""
        if self._users is None:
            from taruvi._sync.modules.users import UsersModule

            self._users = UsersModule(self)
        return self._users

    @property
    def analytics(self):
        """Access Analytics API for executing analytics queries."""
        if self._analytics is None:
            from taruvi._sync.modules.analytics import AnalyticsModule

            self._analytics = AnalyticsModule(self)
        return self._analytics

    def close(self) -> None:
        """Close the client and release resources."""
        self._http_client.close()

    def __enter__(self):
        """Support async context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close client on context exit."""
        self.close()

    def __repr__(self) -> str:
        """String representation of client."""
        mode = self._config.runtime_mode.value
        return (
            f"AsyncClient(api_url={self._config.api_url}, "
            f"site_slug={self._config.site_slug}, "
            f"mode={mode})"
        )
