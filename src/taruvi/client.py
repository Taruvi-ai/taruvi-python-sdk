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
        app_slug: str,
        *,
        # Authentication Methods (All Optional)
        api_key: Optional[str] = None,
        jwt: Optional[str] = None,
        session_token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        # Configuration
        timeout: int = 30,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> None:
        """
        Initialize Taruvi async client with flexible authentication.

        Args:
            api_url: Taruvi API base URL (e.g., "http://localhost:8000")
            app_slug: Application slug (required)
            api_key: Knox API key for authentication (optional)
            jwt: JWT token for authentication (optional)
            session_token: Allauth session token (optional)
            username: Username for auto-login (optional)
            password: Password for auto-login (optional)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            **kwargs: Additional configuration options

        Raises:
            ConfigurationError: If required configuration is missing
        """
        import os

        # Auto-login if username+password provided
        if username and password:
            import httpx
            login_response = httpx.post(
                f"{api_url}/api/auth/login",
                json={"username": username, "password": password}
            )
            login_response.raise_for_status()
            login_data = login_response.json()
            # Store JWT in jwt parameter (overrides any user-provided jwt)
            jwt = login_data.get("access") or login_data.get("token")

        # Load from function runtime if NO auth provided
        elif not any([api_key, jwt, session_token]):
            if os.getenv("TARUVI_FUNCTION_RUNTIME") == "true":
                jwt = os.getenv("TARUVI_FUNCTION_KEY")
                # Also load other function context if not provided
                api_url = api_url or os.getenv("TARUVI_API_URL")
                app_slug = app_slug or os.getenv("TARUVI_APP_SLUG")

        # Use factory method - handles runtime detection and merging
        self._config = TaruviConfig.from_runtime_and_params(
            api_url=api_url,
            app_slug=app_slug,
            api_key=api_key,
            jwt=jwt,  # JWT from: user, login, or function runtime
            session_token=session_token,
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
    app_slug: str,
    *,
    mode: Literal['async'],
    api_key: Optional[str] = None,
    jwt: Optional[str] = None,
    session_token: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    timeout: int = 30,
    max_retries: int = 3,
    **kwargs: Any,
) -> _AsyncClient: ...


@overload
def Client(
    api_url: str,
    app_slug: str,
    *,
    mode: Literal['sync'] = 'sync',
    api_key: Optional[str] = None,
    jwt: Optional[str] = None,
    session_token: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    timeout: int = 30,
    max_retries: int = 3,
    **kwargs: Any,
) -> "_SyncClient": ...


def Client(
    api_url: str,
    app_slug: str,
    mode: str = 'sync',
    **config: Any
) -> Union[_AsyncClient, "_SyncClient"]:
    """
    Create a Taruvi client with flexible authentication.

    Mandatory Parameters:
        api_url: Taruvi API base URL
        app_slug: Application slug

    Optional Parameters:
        mode: Client mode - 'sync' (default) or 'async'

    Authentication (choose ONE or none):
        api_key: Knox API-Key → Authorization: Api-Key {key}
        jwt: JWT Bearer → Authorization: Bearer {jwt}
        session_token: Session → X-Session-Token: {token}
        username+password: Auto-login → Authorization: Bearer {jwt}
        (none): Django session → httpx cookies (automatic)

    Configuration:
        timeout: Request timeout in seconds (default: 30)
        max_retries: Maximum retry attempts (default: 3)

    Returns:
        Configured client instance (_AsyncClient or _SyncClient)

    Examples:
        # Knox API-Key
        client = Client(api_url="...", app_slug="...", api_key="knox_key")

        # JWT Bearer
        client = Client(api_url="...", app_slug="...", jwt="jwt_token")

        # Session Token
        client = Client(api_url="...", app_slug="...", session_token="session")

        # Auto-Login with username+password
        client = Client(
            api_url="...",
            app_slug="...",
            username="alice@example.com",
            password="secret"
        )

        # Django Session (no auth)
        client = Client(api_url="...", app_slug="...")

        # Async mode
        client = Client(api_url="...", app_slug="...", mode='async', jwt="token")
        result = await client.functions.execute("my-function", params={})

    Raises:
        ValueError: If mode is not 'sync' or 'async'
    """
    if mode == 'async':
        return _AsyncClient(api_url, app_slug, **config)
    elif mode == 'sync':
        from taruvi.sync_client import _SyncClient
        return _SyncClient(api_url, app_slug, **config)
    else:
        raise ValueError(
            f"Invalid mode: '{mode}'. Must be 'sync' or 'async'. "
            f"Use Client(mode='sync') for synchronous or Client(mode='async') for async/await."
        )
