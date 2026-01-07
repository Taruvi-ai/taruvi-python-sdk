"""
Taruvi Python SDK

Official SDK for interacting with the Taruvi Cloud Platform.

Unified Client API with flexible authentication:
- **Client(mode='async')**: Async client for async frameworks (uses httpx.AsyncClient)
- **Client(mode='sync')**: Native blocking client for scripts, functions, and notebooks (uses httpx.Client)
- **Client()**: Defaults to sync mode

**Note**: Sync mode uses native httpx.Client (blocking) - NOT asyncio.run() wrapper.
This makes it thread-safe, faster (10-50x), and compatible with all Python environments
including Jupyter notebooks, FastAPI apps, and any async context.

Authentication Methods (All Optional):
1. **Knox API-Key**: Pass `api_key` parameter
2. **JWT Bearer**: Pass `jwt` parameter
3. **Session Token**: Pass `session_token` parameter
4. **Username+Password**: Pass `username` and `password` (auto-login)
5. **Django Session**: No auth parameters (httpx handles cookies automatically)

Authentication Examples:
    ```python
    from taruvi import Client

    # Method 1: Knox API-Key
    client = Client(
        api_url="http://localhost:8000",
        app_slug="my-app",
        api_key="knox_api_key_here"
    )

    # Method 2: JWT Bearer Token
    client = Client(
        api_url="http://localhost:8000",
        app_slug="my-app",
        jwt="jwt_token_here"
    )

    # Method 3: Session Token
    client = Client(
        api_url="http://localhost:8000",
        app_slug="my-app",
        session_token="session_token_here"
    )

    # Method 4: Username+Password (Auto-Login)
    client = Client(
        api_url="http://localhost:8000",
        app_slug="my-app",
        username="alice@example.com",
        password="secret123"
    )

    # Method 5: Django Session (No Auth)
    client = Client(
        api_url="http://localhost:8000",
        app_slug="my-app"
    )
    # httpx automatically sends session cookies
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
    users = client.database.query("users").limit(10).get()
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
        users = client.database.query("users").limit(10).get()

        return {"result": result, "user_count": len(users)}
    ```
"""

from taruvi.client import Client
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
]
