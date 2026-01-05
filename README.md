# Taruvi Python SDK

Official Python SDK for the Taruvi Cloud Platform.

## Features

- **Dual-Mode Operation**: Works seamlessly in both external applications and inside Taruvi functions
- **Auto-Configuration**: Automatically detects runtime environment and configures itself
- **Async & Sync Clients**: Full async/await support (`Client`) and native blocking client (`SyncClient`)
  - **SyncClient**: Native httpx.Client (blocking) - NOT asyncio.run() wrapper
  - **Performance**: 10-50x faster for high-frequency usage
  - **Compatibility**: Works in Jupyter, FastAPI, and all Python environments
- **Type Hints**: Comprehensive type annotations for IDE autocomplete
- **Retry Logic**: Automatic retries with exponential backoff
- **Connection Pooling**: Efficient HTTP connection management
- **Comprehensive Error Handling**: Detailed exceptions for all error cases

## Installation

```bash
pip install taruvi
```

For development:

```bash
pip install -e /path/to/taruvi-sdk
```

## Quick Start

### External Application (Async)

```python
import asyncio
from taruvi import Client

async def main():
    # Create client with explicit configuration
    client = Client(
        api_url="http://localhost:8000",
        api_key="your_jwt_token",
        site_slug="your-site",
        app_slug="your-app"  # Optional
    )

    # Execute a function
    result = await client.functions.execute(
        "process-order",
        params={"order_id": 123, "action": "ship"}
    )
    print(result["data"])

    # Query database
    users = await client.database.query("users") \
        .filter("is_active", "eq", True) \
        .sort("created_at", "desc") \
        .limit(10) \
        .get()

    for user in users:
        print(f"User: {user['name']}")

    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### Inside Taruvi Function (Sync)

```python
# User function uploaded to Taruvi
def main(params, user_data):
    """This function runs inside the Taruvi platform."""
    from taruvi import SyncClient

    # Auto-configures from runtime environment!
    client = SyncClient()

    # Call another function
    result = client.functions.execute(
        "helper-function",
        params={"data": params.get("value")}
    )

    # Query database
    orders = client.database.query("orders") \
        .filter("user_id", "eq", user_data["id"]) \
        .filter("status", "eq", "pending") \
        .get()

    return {
        "helper_result": result["data"],
        "pending_orders": len(orders)
    }
```

## API Reference

### Client

#### Initialization

```python
# External application (explicit config)
client = Client(
    api_url="http://localhost:8000",
    api_key="your_jwt_token",
    site_slug="your-site",
    app_slug="your-app",  # Optional
    timeout=30,
    max_retries=3,
    debug=False
)

# Inside function (auto-configured)
client = Client()  # Or SyncClient() for sync
```

#### Functions API

```python
# Execute a function
result = await client.functions.execute(
    function_slug="my-function",
    params={"key": "value"},
    app_slug="my-app",  # Optional
    is_async=False  # True for async execution
)

# List functions
functions = await client.functions.list(
    app_slug="my-app",
    limit=100,
    offset=0
)

# Get function details
func = await client.functions.get(
    function_slug="my-function",
    app_slug="my-app"
)

# Get invocation status
invocation = await client.functions.get_invocation(
    invocation_id="task_123",
    app_slug="my-app"
)

# List invocations
invocations = await client.functions.list_invocations(
    function_slug="my-function",
    status="completed",  # pending, running, completed, failed
    limit=100
)
```

#### Database API

```python
# Query builder
users = await client.database.query("users") \
    .filter("is_active", "eq", True) \
    .filter("age", "gte", 18) \
    .sort("created_at", "desc") \
    .limit(10) \
    .offset(0) \
    .populate("profile", "orders") \
    .get()

# Filter operators
# eq, gt, gte, lt, lte, in, nin, contains, startswith, endswith, between, null

# Get first result
user = await client.database.query("users") \
    .filter("email", "eq", "alice@example.com") \
    .first()

# Count results
count = await client.database.query("users") \
    .filter("is_active", "eq", True") \
    .count()

# Create record
new_user = await client.database.create(
    table_name="users",
    data={"name": "Alice", "email": "alice@example.com"}
)

# Update record
updated_user = await client.database.update(
    table_name="users",
    record_id=123,
    data={"is_active": False}
)

# Delete record
await client.database.delete(
    table_name="users",
    record_id=123
)
```

#### Storage API

```python
# =====================================
# Bucket Management
# =====================================

# List all buckets
response = await client.storage.list_buckets()
buckets = response["results"]
total = response["count"]

# List buckets with filters
response = await client.storage.list_buckets(
    search="images",
    visibility="public",  # public or private
    app_category="assets",  # assets or attachments
    ordering="-created_at",  # Sort by created_at descending
    page=1,
    page_size=20
)

# Create a new bucket
bucket = await client.storage.create_bucket(
    name="User Uploads",
    slug="user-uploads",  # Optional, auto-generated if not provided
    visibility="private",  # public or private (default: private)
    file_size_limit=10485760,  # 10MB in bytes
    allowed_mime_types=["image/jpeg", "image/png", "image/webp"],
    app_category="assets"  # assets or attachments
)

# Get bucket details
bucket = await client.storage.get_bucket("my-bucket")
print(f"Bucket: {bucket['name']}")
print(f"Objects: {bucket['object_count']}")

# Update bucket settings
updated_bucket = await client.storage.update_bucket(
    "my-bucket",
    visibility="public",
    file_size_limit=104857600  # 100MB
)

# Delete a bucket (and all its objects)
await client.storage.delete_bucket("old-bucket")

# =====================================
# Object Operations
# =====================================

# Upload files
with open("avatar.jpg", "rb") as f1, open("banner.jpg", "rb") as f2:
    uploaded_files = await client.storage.from_("my-bucket").upload(
        files=[("avatar.jpg", f1), ("banner.jpg", f2)],
        paths=["users/123/avatar.jpg", "users/123/banner.jpg"],
        metadatas=[
            {"description": "User avatar"},
            {"description": "Profile banner"}
        ]
    )

# Download a file
file_content = await client.storage.from_("my-bucket").download(
    "users/123/avatar.jpg"
)

# List objects in bucket with filters
response = await client.storage.from_("my-bucket").filter(
    search="avatar",
    mimetype="image/jpeg",
    visibility="public",
    ordering="-created_at",
    page=1,
    page_size=50
).list()

objects = response["data"]
total = response["total"]

# Copy object within same bucket
new_obj = await client.storage.from_("my-bucket").copy_object(
    source_path="users/123/avatar.jpg",
    destination_path="users/456/avatar.jpg"
)

# Copy object to different bucket
new_obj = await client.storage.from_("uploads").copy_object(
    source_path="temp/document.pdf",
    destination_path="archive/2024/document.pdf",
    destination_bucket="archives"
)

# Move/rename object
moved_obj = await client.storage.from_("my-bucket").move_object(
    source_path="temp/document.pdf",
    destination_path="archive/2024/document.pdf"
)

# Update object metadata
updated_obj = await client.storage.from_("my-bucket").update(
    "users/123/avatar.jpg",
    metadata={"description": "Updated avatar"},
    visibility="public"
)

# Delete objects (bulk delete)
await client.storage.from_("my-bucket").delete([
    "temp/file1.txt",
    "temp/file2.txt",
    "temp/file3.txt"
])
```

#### Auth API

```python
# Login
tokens = await client.auth.login(
    username="alice@example.com",
    password="password123"
)
print(tokens["access"])  # Access token
print(tokens["refresh"])  # Refresh token

# Refresh token
new_token = await client.auth.refresh_token(
    refresh_token=tokens["refresh"]
)

# Verify token
result = await client.auth.verify_token(token=tokens["access"])

# Get current user
user = await client.auth.get_current_user()
print(user["username"])
```

#### User Context Switching

```python
# Service client (admin permissions)
service_client = Client(
    api_url="http://localhost:8000",
    api_key="service_api_key",
    site_slug="my-site"
)

# User-scoped client (user's permissions)
user_client = service_client.as_user(user_jwt="user_token")

# This query respects user's permissions
orders = await user_client.database.query("orders").get()
```

### SyncClient (for Functions)

The `SyncClient` provides a synchronous interface identical to `Client`:

```python
from taruvi import SyncClient

# Inside function
def main(params, user_data):
    client = SyncClient()  # Auto-configured

    # All operations are synchronous
    result = client.functions.execute("func", {"test": True})
    users = client.database.query("users").limit(10).get()

    return {"result": result}
```

## Runtime Detection

The SDK automatically detects whether it's running inside a Taruvi function or externally:

```python
from taruvi import detect_runtime, get_function_context, is_inside_function

# Check runtime mode
mode = detect_runtime()  # RuntimeMode.EXTERNAL or RuntimeMode.FUNCTION

# Check if inside function
if is_inside_function():
    print("Running inside Taruvi function!")

# Get function context (when inside function)
context = get_function_context()
if context:
    print(f"Function: {context['function_name']}")
    print(f"Execution ID: {context['execution_id']}")

# Get all execution metadata
metadata = get_execution_metadata()
print(f"Mode: {metadata['mode']}")
```

## Error Handling

The SDK provides detailed exceptions for all error cases:

```python
from taruvi import (
    TaruviError,
    ConfigurationError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ConnectionError,
    FunctionExecutionError
)

try:
    result = await client.functions.execute("my-function", params)
except NotFoundError as e:
    print(f"Function not found: {e.message}")
    print(f"Status: {e.status_code}")
except ValidationError as e:
    print(f"Invalid params: {e.message}")
    print(f"Details: {e.details}")
except AuthorizationError as e:
    print(f"Permission denied: {e.message}")
except TimeoutError as e:
    print(f"Request timed out: {e.message}")
except TaruviError as e:
    print(f"SDK error: {e.message}")
    print(f"Error dict: {e.to_dict()}")
```

## Configuration

### Environment Variables

The SDK can be configured via environment variables:

```bash
# Required
export TARUVI_API_URL="http://localhost:8000"
export TARUVI_API_KEY="your_jwt_token"
export TARUVI_SITE_SLUG="your-site"

# Optional
export TARUVI_APP_SLUG="your-app"
export TARUVI_TIMEOUT=30
export TARUVI_MAX_RETRIES=3
export TARUVI_DEBUG=true

# Function runtime (automatically set by platform)
export TARUVI_FUNCTION_RUNTIME=true
export TARUVI_FUNCTION_ID="fn_123"
export TARUVI_FUNCTION_KEY="function_jwt_token"
```

### .env File

Create a `.env` file in your project root:

```
TARUVI_API_URL=http://localhost:8000
TARUVI_API_KEY=your_jwt_token
TARUVI_SITE_SLUG=your-site
TARUVI_APP_SLUG=your-app
```

Then use the SDK without explicit configuration:

```python
from taruvi import Client

client = Client()  # Loads from .env
```

## Advanced Usage

### Context Manager

```python
# Async
async with Client(api_url="...", api_key="...") as client:
    result = await client.functions.execute("func", {})

# Sync
with SyncClient(api_url="...", api_key="...") as client:
    result = client.functions.execute("func", {})
```

### Custom Timeout and Retries

```python
client = Client(
    api_url="...",
    api_key="...",
    timeout=60,  # 60 seconds
    max_retries=5,
    retry_backoff_factor=1.0  # Exponential backoff
)
```

### Debug Mode

```python
client = Client(
    api_url="...",
    api_key="...",
    debug=True  # Enables detailed logging
)
```

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/taruvi/taruvi-python-sdk
cd taruvi-python-sdk

# Install dependencies
pip install -e ".[dev]"
```

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=taruvi --cov-report=html

# Run specific test
pytest tests/test_client.py -v
```

### Code Quality

```bash
# Format code
black src/

# Lint code
ruff check src/

# Type checking
mypy src/
```

## Examples

See the `examples/` directory for complete examples:

- `external_app.py` - Using SDK in external application
- `function_example.py` - Using SDK inside Taruvi function
- `database_queries.py` - Database query examples
- `error_handling.py` - Error handling patterns

## License

MIT License - See LICENSE file for details

## Support

- **Documentation**: https://docs.taruvi.cloud
- **Issues**: https://github.com/taruvi/taruvi-python-sdk/issues
- **Email**: support@taruvi.cloud
