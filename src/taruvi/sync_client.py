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
        Initialize native synchronous Taruvi client with flexible authentication.

        Args:
            api_url: Taruvi API base URL
            app_slug: Application slug (required)
            api_key: Knox API key for authentication (optional)
            jwt: JWT token for authentication (optional)
            session_token: Allauth session token (optional)
            username: Username for auto-login (optional)
            password: Password for auto-login (optional)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            **kwargs: Additional configuration options
        """
        import os

        # Auto-login if username+password provided (synchronous HTTP call)
        if username and password:
            import httpx
            with httpx.Client() as client:
                login_response = client.post(
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
