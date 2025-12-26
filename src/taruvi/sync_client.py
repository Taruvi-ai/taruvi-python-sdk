"""
Synchronous Client Wrapper

Provides a synchronous interface to the async Taruvi client.
Ideal for use inside Taruvi functions which run synchronously.
"""

import asyncio
from typing import Any, Optional

from taruvi.client import Client
from taruvi.config import TaruviConfig


class SyncFunctionsModule:
    """Synchronous wrapper for Functions API."""

    def __init__(self, async_module) -> None:
        self._async_module = async_module

    def execute(
        self,
        function_slug: str,
        params: Optional[dict[str, Any]] = None,
        *,
        app_slug: Optional[str] = None,
        is_async: bool = False,
        timeout: Optional[int] = None,
    ) -> dict[str, Any]:
        """Execute a function (sync version)."""
        return asyncio.run(
            self._async_module.execute(
                function_slug,
                params,
                app_slug=app_slug,
                is_async=is_async,
                timeout=timeout,
            )
        )

    def list(
        self,
        *,
        app_slug: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List functions (sync version)."""
        return asyncio.run(
            self._async_module.list(app_slug=app_slug, limit=limit, offset=offset)
        )

    def get(
        self,
        function_slug: str,
        *,
        app_slug: Optional[str] = None,
    ) -> dict[str, Any]:
        """Get function details (sync version)."""
        return asyncio.run(self._async_module.get(function_slug, app_slug=app_slug))

    def get_invocation(
        self,
        invocation_id: str,
        *,
        app_slug: Optional[str] = None,
    ) -> dict[str, Any]:
        """Get invocation details (sync version)."""
        return asyncio.run(
            self._async_module.get_invocation(invocation_id, app_slug=app_slug)
        )

    def list_invocations(
        self,
        *,
        function_slug: Optional[str] = None,
        app_slug: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List invocations (sync version)."""
        return asyncio.run(
            self._async_module.list_invocations(
                function_slug=function_slug,
                app_slug=app_slug,
                status=status,
                limit=limit,
                offset=offset,
            )
        )


class SyncQueryBuilder:
    """Synchronous wrapper for QueryBuilder."""

    def __init__(self, async_builder) -> None:
        self._async_builder = async_builder

    def filter(self, field: str, operator: str, value: Any) -> "SyncQueryBuilder":
        """Add filter (sync version)."""
        self._async_builder.filter(field, operator, value)
        return self

    def sort(self, field: str, order: str = "asc") -> "SyncQueryBuilder":
        """Add sorting (sync version)."""
        self._async_builder.sort(field, order)
        return self

    def limit(self, limit: int) -> "SyncQueryBuilder":
        """Limit results (sync version)."""
        self._async_builder.limit(limit)
        return self

    def offset(self, offset: int) -> "SyncQueryBuilder":
        """Set offset (sync version)."""
        self._async_builder.offset(offset)
        return self

    def populate(self, *fields: str) -> "SyncQueryBuilder":
        """Populate related fields (sync version)."""
        self._async_builder.populate(*fields)
        return self

    def get(self) -> list[dict[str, Any]]:
        """Execute query and get results (sync version)."""
        return asyncio.run(self._async_builder.get())

    def first(self) -> Optional[dict[str, Any]]:
        """Get first result (sync version)."""
        return asyncio.run(self._async_builder.first())

    def count(self) -> int:
        """Count results (sync version)."""
        return asyncio.run(self._async_builder.count())


class SyncDatabaseModule:
    """Synchronous wrapper for Database API."""

    def __init__(self, async_module) -> None:
        self._async_module = async_module

    def query(self, table_name: str, app_slug: Optional[str] = None) -> SyncQueryBuilder:
        """Create query builder (sync version)."""
        async_builder = self._async_module.query(table_name, app_slug)
        return SyncQueryBuilder(async_builder)

    def create(
        self,
        table_name: str,
        data: dict[str, Any],
        *,
        app_slug: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create record (sync version)."""
        return asyncio.run(
            self._async_module.create(table_name, data, app_slug=app_slug)
        )

    def update(
        self,
        table_name: str,
        record_id: str | int,
        data: dict[str, Any],
        *,
        app_slug: Optional[str] = None,
    ) -> dict[str, Any]:
        """Update record (sync version)."""
        return asyncio.run(
            self._async_module.update(table_name, record_id, data, app_slug=app_slug)
        )

    def delete(
        self,
        table_name: str,
        record_id: str | int,
        *,
        app_slug: Optional[str] = None,
    ) -> dict[str, Any]:
        """Delete record (sync version)."""
        return asyncio.run(
            self._async_module.delete(table_name, record_id, app_slug=app_slug)
        )


class SyncAuthModule:
    """Synchronous wrapper for Auth API."""

    def __init__(self, async_module) -> None:
        self._async_module = async_module

    def login(self, username: str, password: str) -> dict[str, Any]:
        """Login (sync version)."""
        return asyncio.run(self._async_module.login(username, password))

    def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """Refresh token (sync version)."""
        return asyncio.run(self._async_module.refresh_token(refresh_token))

    def verify_token(self, token: str) -> dict[str, Any]:
        """Verify token (sync version)."""
        return asyncio.run(self._async_module.verify_token(token))

    def get_current_user(self) -> dict[str, Any]:
        """Get current user (sync version)."""
        return asyncio.run(self._async_module.get_current_user())


class SyncClient:
    """
    Synchronous Taruvi API Client.

    This client wraps the async Client and provides a synchronous interface.
    Ideal for use inside Taruvi functions which run synchronously.

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
        **kwargs: Any,
    ) -> None:
        """
        Initialize synchronous Taruvi client.

        Args:
            api_url: Taruvi API base URL
            api_key: JWT token for authentication
            site_slug: Site slug for multi-tenant routing
            app_slug: App slug (optional)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            retry_backoff_factor: Backoff factor for retries
            debug: Enable debug logging
            **kwargs: Additional configuration options
        """
        # Create async client
        self._async_client = Client(
            api_url=api_url,
            api_key=api_key,
            site_slug=site_slug,
            app_slug=app_slug,
            timeout=timeout,
            max_retries=max_retries,
            retry_backoff_factor=retry_backoff_factor,
            debug=debug,
            **kwargs,
        )

        # Create sync wrappers for modules
        self._functions = None
        self._database = None
        self._auth = None

    @property
    def config(self) -> TaruviConfig:
        """Get client configuration."""
        return self._async_client.config

    @property
    def functions(self) -> SyncFunctionsModule:
        """Access Functions API (sync)."""
        if self._functions is None:
            self._functions = SyncFunctionsModule(self._async_client.functions)
        return self._functions

    @property
    def database(self) -> SyncDatabaseModule:
        """Access Database API (sync)."""
        if self._database is None:
            self._database = SyncDatabaseModule(self._async_client.database)
        return self._database

    @property
    def auth(self) -> SyncAuthModule:
        """Access Auth API (sync)."""
        if self._auth is None:
            self._auth = SyncAuthModule(self._async_client.auth)
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
            api_url=self.config.api_url,
            api_key=user_jwt,
            site_slug=self.config.site_slug,
            app_slug=self.config.app_slug,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
            retry_backoff_factor=self.config.retry_backoff_factor,
            debug=self.config.debug,
            user_jwt=user_jwt,
        )

    def close(self) -> None:
        """Close the client and release resources."""
        asyncio.run(self._async_client.close())

    def __enter__(self):
        """Support context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close client on context exit."""
        self.close()

    def __repr__(self) -> str:
        """String representation of client."""
        return f"Sync{self._async_client!r}"
