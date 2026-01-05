"""
Taruvi Python SDK

Official SDK for interacting with the Taruvi Cloud Platform.

Unified Client API with mode parameter:
- **Client(mode='async')**: Async client for async frameworks (uses httpx.AsyncClient)
- **Client(mode='sync')**: Native blocking client for scripts, functions, and notebooks (uses httpx.Client)
- **Client()**: Defaults to sync mode

**Note**: Sync mode uses native httpx.Client (blocking) - NOT asyncio.run() wrapper.
This makes it thread-safe, faster (10-50x), and compatible with all Python environments
including Jupyter notebooks, FastAPI apps, and any async context.

Async Client Example:
    ```python
    from taruvi import Client

    async def main():
        client = Client(
            mode='async',
            app_slug="my-app",
            api_url="http://localhost:8000",
            api_key="your_jwt_token",
            site_slug="your-site"
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
        app_slug="my-app",
        api_url="http://localhost:8000",
        api_key="your_jwt_token",
        site_slug="your-site"
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

        client = Client(app_slug="my-app")  # Defaults to sync mode

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
from taruvi.models.auth import TokenResponse, UserResponse, UserListResponse
from taruvi.models.database import DatabaseRecord
from taruvi.models.functions import (
    FunctionExecutionResult,
    FunctionListResponse,
    FunctionResponse,
    InvocationResponse,
)
from taruvi.models.storage import StorageObject, StorageListResponse
from taruvi.models.secrets import Secret, SecretListResponse
from taruvi.models.policy import PolicyCheckResponse, ResourceCheckRequest
from taruvi.models.app import Role, RoleListResponse, UserApp
from taruvi.models.settings import SiteSettings
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
    # Response Models - Auth
    "TokenResponse",
    "UserResponse",
    "UserListResponse",
    # Response Models - Functions
    "FunctionResponse",
    "FunctionExecutionResult",
    "FunctionListResponse",
    "InvocationResponse",
    # Response Models - Database
    "DatabaseRecord",
    # Response Models - Storage
    "StorageObject",
    "StorageListResponse",
    # Response Models - Secrets
    "Secret",
    "SecretListResponse",
    # Response Models - Policy
    "PolicyCheckResponse",
    "ResourceCheckRequest",
    # Response Models - App
    "Role",
    "RoleListResponse",
    "UserApp",
    # Response Models - Settings
    "SiteSettings",
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
