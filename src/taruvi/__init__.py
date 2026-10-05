"""
Taruvi Python SDK

Official SDK for interacting with the Taruvi Cloud Platform.

Unified Client API:
- **Client(api_url, app_slug, mode='async')**: Async client for async frameworks (uses httpx.AsyncClient)
- **Client(api_url, app_slug, mode='sync')**: Native blocking client for scripts, functions, and notebooks (uses httpx.Client)
- **Client(api_url, app_slug)**: Sync outside a running event loop, async inside one

**Note**: Sync mode uses native httpx.Client (blocking) - NOT asyncio.run() wrapper.
This makes it thread-safe and compatible with Jupyter notebooks and web workers.

Authentication:
Create a client, then call ``client.auth`` to get a new authenticated client.
Credentials can also be passed as keyword arguments or ``TARUVI_*`` environment
variables (for example ``api_key=`` or ``TARUVI_API_KEY``).

Authentication Examples:
    ```python
    from taruvi import Client

    # Step 1: Create unauthenticated client
    client = Client(
        api_url="https://api.example.com",
        app_slug="my-app"
    )

    # Step 2: Authenticate

    # Method 1: JWT Bearer Token
    auth_client = client.auth.signInWithToken(
        token="jwt_token_here",
        token_type="jwt"
    )

    # Method 2: API key
    auth_client = client.auth.signInWithToken(
        token="api_key_here",
        token_type="api_key"
    )

    # Method 3: Session Token
    auth_client = client.auth.signInWithToken(
        token="session_token_here",
        token_type="session_token"
    )

    # Method 4: Email and password
    auth_client = client.auth.signInWithPassword(
        email="alice@example.com",
        password="secret123"
    )

    # Now use auth_client for authenticated requests
    result = auth_client.functions.execute("my-func", params={})
    ```

Async Client Example:
    ```python
    from taruvi import Client

    async def main():
        client = Client(
            api_url="https://api.example.com",
            app_slug="my-app",
            mode="async",
            api_key="your_api_key",
        )

        # Execute a function
        result = await client.functions.execute(
            "process-data",
            params={"value": 42}
        )
        print(result["data"])

        await client.close()
    ```

Sync Client Example:
    ```python
    from taruvi import Client

    client = Client(
        api_url="https://api.example.com",
        app_slug="my-app",
        mode="sync",
        api_key="your_api_key",
    )

    # Direct blocking calls (no asyncio.run)
    result = client.functions.execute("process-data", params={"value": 42})
    users = client.database.from_("users").page_size(10).execute()
    ```

Function Runtime Example:
    ```python
    # Inside a Taruvi function, the platform passes an authenticated client.
    def main(params, user_data, sdk_client):
        # Call another function
        result = sdk_client.functions.execute("helper", params={"test": True})

        # Query database
        users = sdk_client.database.from_("users").page_size(10).execute()

        return {"result": result, "user_count": len(users["data"])}
    ```
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Literal, Optional, Union, overload

from taruvi._modes import RuntimeMode
from taruvi._version import __version__ as __version__
from taruvi.exceptions import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    BillingError,
    ConfigurationError,
    ConflictError,
    ConnectionError,
    FunctionExecutionError,
    GatewayTimeoutError,
    NetworkError,
    NotAuthenticatedError,
    NotFoundError,
    RateLimitError,
    ResponseError,
    RuntimeError,
    ServerError,
    ServiceUnavailableError,
    TaruviError,
    TimeoutError,
    ValidationError,
)
from taruvi.runtime import (
    detect_runtime,
    get_execution_metadata,
    get_function_context,
    is_inside_function,
)
from taruvi.types import (
    AnalyticsQueryResult,
    App,
    Bucket,
    # Filter types
    DatabaseFilters,
    DatabaseRecord,
    Function,
    FunctionExecutionResponse,
    FunctionFilters,
    FunctionInvocation,
    FunctionInvocationListResponse,
    FunctionListResponse,
    FunctionTaskResult,
    FunctionTaskResultResponse,
    PaginatedResponse,
    PgRangeValue,
    PolicyCheckBatchResult,
    PolicyCheckResult,
    Secret,
    SecretFilters,
    Setting,
    StorageAccessLinkResult,
    StorageBrowseData,
    StorageBrowseFile,
    StorageBrowseFolder,
    StorageFile,
    StorageFilters,
    # Response types
    User,
    UserFilters,
    UserResponse,
)

if TYPE_CHECKING:
    from taruvi._async.client import AsyncClient
    from taruvi._sync.client import SyncClient
    from taruvi.config import TaruviConfig

# Names resolved lazily by __getattr__ (PEP 562). TaruviConfig pulls in
# pydantic_settings, which is expensive to import (entry-point scanning etc.)
# and is only needed once a Client is constructed or the config is used
# directly, so `import taruvi` does not pay for it.
_LAZY_ATTRS = {
    "TaruviConfig": "taruvi.config",
}


def __getattr__(name: str) -> Any:
    module_name = _LAZY_ATTRS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    import importlib

    value = getattr(importlib.import_module(module_name), name)
    globals()[name] = value  # cache so __getattr__ is not hit again
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_LAZY_ATTRS))


def _is_async_context() -> bool:
    """Detect if we're in an async context."""
    # In test mode, default to sync (tests must explicitly specify mode='async')
    if os.getenv("TARUVI_TEST_MODE") == "true":
        return False

    # Imported here rather than at module level: this is the only use of
    # asyncio in the package and importing it costs tens of ms (hundreds
    # under gVisor), which the sync-only path should not pay.
    import asyncio
    import builtins

    try:
        asyncio.get_running_loop()
        return True
    except builtins.RuntimeError:
        # Must be the builtin: `RuntimeError` in this module's namespace is
        # taruvi.exceptions.RuntimeError (re-exported above), which does not
        # catch the builtin raised by get_running_loop() when no loop runs.
        return False


@overload
def Client(
    api_url: str,
    app_slug: str,
    *,
    mode: Literal["sync"],
    timeout: int = 120,
    max_retries: int = 3,
    **kwargs: Any,
) -> SyncClient: ...


@overload
def Client(
    api_url: str,
    app_slug: str,
    *,
    mode: Literal["async"],
    timeout: int = 120,
    max_retries: int = 3,
    **kwargs: Any,
) -> AsyncClient: ...


@overload
def Client(
    api_url: str,
    app_slug: str,
    *,
    mode: Optional[str] = None,
    timeout: int = 120,
    max_retries: int = 3,
    **kwargs: Any,
) -> Union[AsyncClient, SyncClient]: ...


def Client(
    api_url: str,
    app_slug: str,
    *,
    mode: Optional[str] = None,
    timeout: int = 120,
    max_retries: int = 3,
    **kwargs: Any,
) -> Union[AsyncClient, SyncClient]:
    """
    Create a Taruvi client (unified factory).

    Mandatory Parameters:
        api_url: Taruvi API base URL
        app_slug: Application slug

    Optional Parameters:
        mode: Client mode - 'sync' (default) or 'async' (auto-detected if not specified)
        timeout: Request timeout in seconds (default: 120)
        max_retries: Maximum retry attempts (default: 3)

    Returns:
        AsyncClient or SyncClient depending on mode

    Examples:
        # Auto-detect mode (sync in normal context, async in event loop)
        client = Client(
            api_url="https://api.taruvi.cloud",
            app_slug="my-app"
        )

        # Force sync mode
        client = Client(
            api_url="https://api.taruvi.cloud",
            app_slug="my-app",
            mode='sync'
        )

        # Force async mode
        client = Client(
            api_url="https://api.taruvi.cloud",
            app_slug="my-app",
            mode='async'
        )
    """
    # Auto-detect mode if not specified
    if mode is None:
        mode = "async" if _is_async_context() else "sync"

    # Return appropriate client
    if mode == "async":
        from taruvi._async.client import AsyncClient

        return AsyncClient(api_url, app_slug, timeout=timeout, max_retries=max_retries, **kwargs)
    elif mode == "sync":
        from taruvi._sync.client import SyncClient

        return SyncClient(api_url, app_slug, timeout=timeout, max_retries=max_retries, **kwargs)
    else:
        raise ValueError(
            f"Invalid mode: '{mode}'. Must be 'sync' or 'async'. "
            f"Use Client(mode='sync') for synchronous or Client(mode='async') for async/await."
        )


__all__ = [  # noqa: RUF022 - grouped by kind on purpose
    # Main client
    "Client",
    # Configuration
    "TaruviConfig",
    "RuntimeMode",
    # Runtime detection
    "detect_runtime",
    "is_inside_function",
    "get_function_context",
    "get_execution_metadata",
    # Exceptions
    "TaruviError",
    "ConfigurationError",
    "APIError",
    "ValidationError",
    "AuthenticationError",
    "NotAuthenticatedError",
    "AuthorizationError",
    "NotFoundError",
    "ConflictError",
    "RateLimitError",
    "ServerError",
    "ServiceUnavailableError",
    "GatewayTimeoutError",
    "BillingError",
    "NetworkError",
    "TimeoutError",
    "ConnectionError",
    "RuntimeError",
    "FunctionExecutionError",
    "ResponseError",
    # Response types
    "User",
    "UserResponse",
    "DatabaseRecord",
    "StorageFile",
    "StorageAccessLinkResult",
    "StorageBrowseFolder",
    "StorageBrowseFile",
    "StorageBrowseData",
    "Function",
    "FunctionInvocation",
    "FunctionExecutionResponse",
    "FunctionInvocationListResponse",
    "FunctionListResponse",
    "FunctionTaskResult",
    "FunctionTaskResultResponse",
    "Secret",
    "Bucket",
    "App",
    "Setting",
    "PolicyCheckResult",
    "PolicyCheckBatchResult",
    "AnalyticsQueryResult",
    "PaginatedResponse",
    "PgRangeValue",
    # Filter types
    "DatabaseFilters",
    "StorageFilters",
    "FunctionFilters",
    "SecretFilters",
    "UserFilters",
]
