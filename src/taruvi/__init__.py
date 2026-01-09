"""
Taruvi Python SDK

Official SDK for interacting with the Taruvi Cloud Platform.

Unified Client API:
- **Client(mode='async')**: Async client for async frameworks (uses httpx.AsyncClient)
- **Client(mode='sync')**: Native blocking client for scripts, functions, and notebooks (uses httpx.Client)
- **Client()**: Defaults to sync mode

**Note**: Sync mode uses native httpx.Client (blocking) - NOT asyncio.run() wrapper.
This makes it thread-safe, faster (10-50x), and compatible with all Python environments
including Jupyter notebooks, FastAPI apps, and any async context.

Authentication via AuthManager:
All authentication is handled through the AuthManager after client creation.
This provides a clean separation between client initialization and authentication.

Authentication Examples:
    ```python
    from taruvi import Client

    # Step 1: Create unauthenticated client
    client = Client(
        api_url="http://localhost:8000",
        app_slug="my-app"
    )

    # Step 2: Authenticate using AuthManager

    # Method 1: JWT Bearer Token
    auth_client = client.auth.signInWithToken(
        token="jwt_token_here",
        token_type="jwt"
    )

    # Method 2: Knox API-Key
    auth_client = client.auth.signInWithToken(
        token="knox_api_key_here",
        token_type="api_key"
    )

    # Method 3: Session Token
    auth_client = client.auth.signInWithToken(
        token="session_token_here",
        token_type="session_token"
    )

    # Method 4: Username+Password
    auth_client = client.auth.signInWithPassword(
        username="alice@example.com",
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
            mode='async',
            api_url="http://localhost:8000",
            app_slug="my-app",
            jwt="your_jwt_token"
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

    # Native blocking - works everywhere! (mode='sync' is default)
    client = Client(
        api_url="http://localhost:8000",
        app_slug="my-app",
        jwt="your_jwt_token"
    )

    # Direct blocking calls (no asyncio.run)
    result = client.functions.execute("process-data", params={"value": 42})
    users = client.database.query("users").page_size(10).get()
    ```

Function Runtime Example:
    ```python
    # Inside Taruvi function - auto-configured!
    def main(params, user_data):
        from taruvi import Client

        client = Client()  # Auto-detects from environment

        # Call another function
        result = client.functions.execute("helper", {"test": True})

        # Query database
        users = client.database.query("users").page_size(10).get()

        return {"result": result, "user_count": len(users)}
    ```
"""

from typing import Optional, Any
import asyncio
import os

from taruvi.config import RuntimeMode, TaruviConfig
from taruvi.exceptions import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    ConflictError,
    ConnectionError,
    FunctionExecutionError,
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
    # Response types
    User,
    DatabaseRecord,
    StorageFile,
    Function,
    FunctionInvocation,
    Secret,
    Bucket,
    App,
    Setting,
    PolicyCheckResult,
    PolicyCheckBatchResult,
    PaginatedResponse,
    # Filter types
    DatabaseFilters,
    StorageFilters,
    FunctionFilters,
    SecretFilters,
    UserFilters,
)


def _is_async_context() -> bool:
    """Detect if we're in an async context."""
    # In test mode, default to sync (tests must explicitly specify mode='async')
    if os.getenv("TARUVI_TEST_MODE") == "true":
        return False

    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False


def Client(
    api_url: str,
    app_slug: str,
    *,
    mode: Optional[str] = None,
    timeout: int = 30,
    max_retries: int = 3,
    **kwargs: Any
):
    """
    Create a Taruvi client (unified factory).

    Mandatory Parameters:
        api_url: Taruvi API base URL
        app_slug: Application slug

    Optional Parameters:
        mode: Client mode - 'sync' (default) or 'async' (auto-detected if not specified)
        timeout: Request timeout in seconds (default: 30)
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


__version__ = "0.2.0"

__all__ = [
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
    "NetworkError",
    "TimeoutError",
    "ConnectionError",
    "RuntimeError",
    "FunctionExecutionError",
    "ResponseError",
    # Response types
    "User",
    "DatabaseRecord",
    "StorageFile",
    "Function",
    "FunctionInvocation",
    "Secret",
    "Bucket",
    "App",
    "Setting",
    "PolicyCheckResult",
    "PolicyCheckBatchResult",
    "PaginatedResponse",
    # Filter types
    "DatabaseFilters",
    "StorageFilters",
    "FunctionFilters",
    "SecretFilters",
    "UserFilters",
]
