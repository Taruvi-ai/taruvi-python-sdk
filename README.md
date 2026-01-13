# Taruvi Python SDK

[![PyPI version](https://img.shields.io/pypi/v/taruvi.svg)](https://pypi.org/project/taruvi/)
[![Python versions](https://img.shields.io/pypi/pyversions/taruvi.svg)](https://pypi.org/project/taruvi/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/badge/docs-taruvi.cloud-blue.svg)](https://docs.taruvi.cloud)

Official Python SDK for the Taruvi Cloud Platform - A modern, type-safe SDK for building serverless applications with full async/sync support.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Authentication](#authentication)
- [Usage Examples](#usage-examples)
  - [Functions](#functions)
  - [Database Operations](#database-operations)
  - [User Authentication & Management](#user-authentication--management)
  - [Storage & Files](#storage--files)
  - [Secrets Management](#secrets-management)
  - [Policy & Authorization](#policy--authorization)
- [Async vs Sync](#async-vs-sync)
- [Configuration](#configuration)
- [Error Handling](#error-handling)
- [Advanced Usage](#advanced-usage)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)
- [Support](#support)

---

## Overview

Taruvi Cloud is a multi-tenant Backend-as-a-Service platform that provides:

- **Serverless Functions**: Execute code on-demand with full isolation
- **Database APIs**: Schema-per-tenant data storage with query builder
- **Authentication**: JWT-based auth with role management
- **Storage**: File management with bucket organization
- **Secrets**: Secure credential management with inheritance
- **Policies**: Fine-grained authorization (Cerbos integration)

The Taruvi Python SDK provides a clean, pythonic interface to all platform capabilities with:
- **Full Type Safety**: Complete type hints for IDE autocomplete
- **Dual Runtime Modes**: Both async and native blocking sync support
- **AuthManager Authentication**: Clean separation of client initialization and authentication
- **Production Ready**: Automatic retries, connection pooling, timeout handling

📚 **[Full Documentation](https://docs.taruvi.cloud)** | 🌐 **[Taruvi Cloud](https://taruvi.cloud)**

---

## Features

✨ **Unified Client API**
- Single `Client()` factory supporting both async and sync modes
- Lazy-loaded modules for optimal performance
- Context manager support (`with` / `async with`)

🔐 **AuthManager-Based Authentication**
- Clean separation of client initialization and authentication
- JWT Bearer tokens
- Knox API Keys
- Session tokens
- Username/Password (auto-login)
- Runtime authentication switching

🗃️ **Database Query Builder**
- Fluent API: `client.database.query("users").filter(...).sort(...).get()`
- Pagination with `page_size()` and `page()`
- Foreign key population with `populate()`
- Filtering with operators: eq, gt, lt, gte, lte, ne, contains, etc.

⚡ **High-Performance Sync Client**
- Native `httpx.Client` (blocking) - NOT asyncio wrapper
- 10-50x faster than `asyncio.run()` pattern
- Thread-safe, works in Jupyter, FastAPI, any environment

🔄 **Automatic Retry Logic**
- Exponential backoff (default: 3 retries)
- Configurable timeout (default: 30s)
- Connection pooling (max 10 connections)

🎯 **Type-Safe APIs**
- Complete type hints using Python 3.10+ features
- IDE autocomplete for all methods
- Returns plain `dict[str, Any]` (no complex model classes)

🚀 **Function Runtime Auto-Detection**
- Zero-config when running inside Taruvi functions
- Automatic context inheritance from environment
- Seamless function-to-function calls

---

## Installation

### Using pip

```bash
pip install taruvi
```

### Using Poetry

```bash
poetry add taruvi
```

### Using pipenv

```bash
pipenv install taruvi
```

### Requirements

- **Python**: 3.10 or higher
- **Dependencies** (automatically installed):
  - `httpx>=0.27.0` - Modern HTTP client
  - `pydantic>=2.0.0` - Data validation
  - `pydantic-settings>=2.0.0` - Settings management
  - `python-dotenv>=1.0.0` - Environment variable loading

---

## Quick Start

### Sync Client (Default - Recommended)

```python
from taruvi import Client

# Step 1: Create unauthenticated client
client = Client(
    api_url="https://api.taruvi.cloud",
    app_slug="my-app"
)

# Step 2: Authenticate using AuthManager
auth_client = client.auth.signInWithPassword(
    username="alice@example.com",
    password="secret123"
)

# Step 3: Use authenticated client
result = auth_client.functions.execute("process-order", params={"order_id": 123})
print(result["data"])

# Query database
users = auth_client.database.query("users").page_size(10).get()
print(f"Found {len(users)} users")
```

### Async Client

```python
from taruvi import Client
import asyncio

async def main():
    # Step 1: Create unauthenticated client
    client = Client(
        mode='async',
        api_url="https://api.taruvi.cloud",
        app_slug="my-app"
    )

    # Step 2: Authenticate using AuthManager (not async)
    auth_client = client.auth.signInWithPassword(
        username="alice@example.com",
        password="secret123"
    )

    # Step 3: Use authenticated client
    result = await auth_client.functions.execute("process-order", params={"order_id": 123})
    print(result["data"])

    # Query database
    users = await auth_client.database.query("users").page_size(10).get()
    print(f"Found {len(users)} users")

    await auth_client.close()

asyncio.run(main())
```

### Inside Taruvi Function (Auto-Configured)

```python
# handler.py - Runs inside Taruvi function runtime
from taruvi import Client

def main(params, user_data):
    # Auto-configured from environment variables!
    client = Client(
        api_url="http://localhost:8000",  # Or from TARUVI_API_URL
        app_slug="my-app"  # Or from TARUVI_APP_SLUG
    )

    # Call another function
    result = client.functions.execute("helper", {"test": True})

    # Query database
    users = client.database.query("users").page_size(10).get()

    return {"result": result, "user_count": len(users)}
```

---

## Authentication

### Overview

Taruvi SDK uses **AuthManager** for all authentication. You create an unauthenticated client first, then authenticate using one of the AuthManager methods.

This approach provides:
- ✅ Clean separation of client initialization and authentication
- ✅ Easy authentication switching at runtime
- ✅ Immutable client design (auth methods return new instances)

### Authentication Flow

**Step 1**: Create unauthenticated client
```python
from taruvi import Client

client = Client(
    api_url="https://api.taruvi.cloud",
    app_slug="my-app"
)
```

**Step 2**: Authenticate using AuthManager (choose one method)

---

### Method 1: Username + Password

```python
# Authenticate with username/password
auth_client = client.auth.signInWithPassword(
    username="alice@example.com",
    password="secret123"
)

# SDK performs login and obtains JWT automatically
# Now use auth_client for authenticated requests
```

**What happens**: SDK makes login request, receives JWT, returns new authenticated client
**Header sent**: `Authorization: Bearer {jwt}`

---

### Method 2: JWT Bearer Token

```python
# Authenticate with existing JWT token
auth_client = client.auth.signInWithToken(
    token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    token_type="jwt"
)
```

**Header sent**: `Authorization: Bearer {jwt}`

---

### Method 3: Knox API Key

```python
# Authenticate with Knox API key
auth_client = client.auth.signInWithToken(
    token="knox_api_key_here",
    token_type="api_key"
)
```

**Header sent**: `Authorization: Api-Key {key}`

---

### Method 4: Session Token

```python
# Authenticate with session token
auth_client = client.auth.signInWithToken(
    token="session_token_here",
    token_type="session_token"
)
```

**Header sent**: `X-Session-Token: {token}`

---

### Complete Authentication Example

```python
from taruvi import Client

# Create unauthenticated client
client = Client(
    api_url="https://api.taruvi.cloud",
    app_slug="my-app"
)

# Authenticate with username/password
auth_client = client.auth.signInWithPassword(
    username="alice@example.com",
    password="secret123"
)

# Check authentication status
print(auth_client.is_authenticated)  # True

# Use authenticated client
result = auth_client.functions.execute("my-func", params={})

# Sign out (removes authentication)
unauth_client = auth_client.auth.signOut()
print(unauth_client.is_authenticated)  # False
```

---

### Switching Authentication at Runtime

```python
# Start unauthenticated
client = Client(api_url="...", app_slug="...")

# Authenticate as user 1
user1_client = client.auth.signInWithPassword(
    username="user1@example.com",
    password="pass1"
)

# Switch to user 2
user2_client = user1_client.auth.signInWithPassword(
    username="user2@example.com",
    password="pass2"
)

# Each client is independent and immutable
```

### Environment Variables

You can store credentials in environment variables:

```bash
# .env file
TARUVI_API_URL=https://api.taruvi.cloud
TARUVI_APP_SLUG=my-app
TARUVI_JWT=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
TARUVI_API_KEY=knox_api_key
TARUVI_SESSION_TOKEN=session_token
TARUVI_USERNAME=alice@example.com
TARUVI_PASSWORD=secret123
```

Then use them in your code:

```python
import os
from taruvi import Client

# Create client
client = Client(
    api_url=os.getenv("TARUVI_API_URL"),
    app_slug=os.getenv("TARUVI_APP_SLUG")
)

# Authenticate with credentials from environment
auth_client = client.auth.signInWithPassword(
    username=os.getenv("TARUVI_USERNAME"),
    password=os.getenv("TARUVI_PASSWORD")
)

# Or with token from environment
auth_client = client.auth.signInWithToken(
    token=os.getenv("TARUVI_JWT"),
    token_type="jwt"
)
```

---

## Usage Examples

### Functions

#### Execute Function (Synchronous)

```python
# Synchronous execution (waits for result)
result = client.functions.execute(
    "process-order",
    params={"order_id": 123, "customer_id": 456}
)
print(result["data"])
```

#### Execute Function (Asynchronous with Polling)

```python
import time

# Start async execution (returns immediately with task_id)
result = client.functions.execute(
    "long-running-task",
    params={"data": "large_dataset"},
    is_async=True  # Execute in background
)

task_id = result['invocation']['celery_task_id']
print(f"Task started: {task_id}")

# Poll for result
while True:
    task_result = client.functions.get_result(task_id)
    status = task_result['data']['status']

    if status == 'SUCCESS':
        print("Completed:", task_result['data']['result'])
        break
    elif status == 'FAILURE':
        print("Failed:", task_result['data']['traceback'])
        break
    else:
        print(f"Status: {status}, waiting...")
        time.sleep(2)
```

#### List Functions

```python
# List all functions
functions = client.functions.list(limit=50, offset=0)
for func in functions['results']:
    print(f"{func['name']}: {func['slug']}")
```

#### Get Function Details

```python
# Get specific function
func = client.functions.get("process-order")
print(func['name'], func['execution_mode'])
```

---

### Database Operations

#### Query Builder Pattern

```python
# Simple query
users = client.database.query("users").get()

# With filtering
active_users = (
    client.database.query("users")
    .filter("is_active", "eq", True)
    .filter("age", "gte", 18)
    .get()
)

# With sorting and pagination
users_page = (
    client.database.query("users")
    .filter("email", "contains", "@example.com")
    .sort("created_at", "desc")
    .page_size(20)
    .page(1)
    .get()
)

# Populate foreign keys
orders = (
    client.database.query("orders")
    .populate("customer", "product")  # Load related records
    .get()
)
```

#### Filter Operators

```python
# Supported operators:
.filter("age", "eq", 25)         # Equal
.filter("age", "ne", 25)         # Not equal
.filter("age", "gt", 18)         # Greater than
.filter("age", "gte", 18)        # Greater than or equal
.filter("age", "lt", 65)         # Less than
.filter("age", "lte", 65)        # Less than or equal
.filter("name", "contains", "Alice")  # Contains
.filter("email", "startswith", "test")  # Starts with
.filter("email", "endswith", ".com")    # Ends with
```

#### Get Single Record

```python
# Get by ID
user = client.database.get("users", record_id=123)
print(user['email'])
```

#### Create Records

```python
# Create single record
new_user = client.database.create("users", {
    "email": "alice@example.com",
    "name": "Alice",
    "age": 30
})
print(f"Created user: {new_user['id']}")

# Create multiple records (bulk)
new_users = client.database.create("users", [
    {"email": "bob@example.com", "name": "Bob"},
    {"email": "charlie@example.com", "name": "Charlie"}
])
print(f"Created {len(new_users)} users")
```

#### Update Records

```python
# Update single record
updated = client.database.update(
    "users",
    record_id=123,
    data={"name": "Alice Smith", "age": 31}
)

# Update multiple records
updated_many = client.database.update("users", data=[
    {"id": 123, "name": "Alice Updated"},
    {"id": 456, "name": "Bob Updated"}
])
```

#### Delete Records

```python
# Delete by ID
client.database.delete("users", record_id=123)

# Delete by IDs (bulk)
client.database.delete("users", record_ids=[123, 456, 789])

# Delete by filter
client.database.delete("users", filters={"is_active": False})
```

#### Query Helpers

```python
# Get first result
first_user = client.database.query("users").first()

# Get count
user_count = (
    client.database.query("users")
    .filter("is_active", "eq", True)
    .count()
)
print(f"Active users: {user_count}")
```

---

### User Authentication & Management

#### Login and Token Management

```python
# Login to get JWT tokens
tokens = client.auth.login(
    username="alice@example.com",
    password="secret123"
)
access_token = tokens['access']
refresh_token = tokens['refresh']

# Refresh access token
new_tokens = client.auth.refresh_token(refresh_token)

# Verify token
is_valid = client.auth.verify_token(access_token)
```

#### Get Current User

```python
# Get authenticated user info
user = client.auth.get_current_user()
print(user['username'], user['email'])
```

#### User Management

```python
# List users with filters
users = client.users.list_users(
    search="alice",
    is_active=True,
    roles="admin,editor",
    page=1,
    page_size=20
)

# Get specific user
user = client.users.get_user("alice")

# Create user
new_user = client.users.create_user(
    username="bob",
    email="bob@example.com",
    password="secret456",
    confirm_password="secret456",
    first_name="Bob",
    last_name="Smith",
    is_active=True,
    is_staff=False
)

# Update user
updated = client.users.update_user(
    username="bob",
    email="bob.smith@example.com",
    first_name="Robert"
)

# Delete user
client.users.delete_user("bob")
```

#### Role Management (Bulk Operations)

```python
# Assign roles to multiple users
client.users.assign_roles(
    roles=["editor", "reviewer"],
    usernames=["alice", "bob", "charlie"],
    expires_at="2025-12-31T23:59:59Z"  # Optional expiration
)

# Revoke roles from multiple users
client.users.revoke_roles(
    roles=["editor"],
    usernames=["alice", "bob"]
)

# Get user's apps
apps = client.users.get_user_apps("alice")
```

---

### Storage & Files

#### Bucket Operations

```python
# List buckets
buckets = client.storage.list_buckets()

# Create bucket
bucket = client.storage.create_bucket(
    name="images",
    description="User uploaded images"
)

# Get bucket details
bucket = client.storage.get_bucket("images")

# Update bucket
client.storage.update_bucket("images", {
    "description": "Public user images",
    "visibility": "public"
})

# Delete bucket
client.storage.delete_bucket("images")
```

#### File Operations

```python
# Select bucket and list files
files = (
    client.storage.from_("images")
    .filter("mimetype", "contains", "image/")
    .list()
)

# Upload files (batch)
uploaded = (
    client.storage.from_("images")
    .upload([
        {"file": open("photo1.jpg", "rb"), "name": "photo1.jpg"},
        {"file": open("photo2.jpg", "rb"), "name": "photo2.jpg"}
    ])
)

# Download file
file_data = client.storage.from_("images").download("photo1.jpg")

# Update file metadata
client.storage.from_("images").update("photo1.jpg", {
    "name": "profile-photo.jpg",
    "visibility": "public"
})

# Delete files (batch)
client.storage.from_("images").delete(["photo1.jpg", "photo2.jpg"])

# Copy file
client.storage.from_("images").copy_object(
    "photo1.jpg",
    destination_bucket="backups",
    destination_name="photo1-backup.jpg"
)

# Move file
client.storage.from_("images").move_object(
    "photo1.jpg",
    destination_bucket="archive",
    destination_name="old-photo1.jpg"
)
```

---

### Secrets Management

#### List Secrets with Filters

```python
# List all secrets
secrets = client.secrets.list_secrets()

# List with filters
api_secrets = client.secrets.list_secrets(
    search="API",
    secret_type="api_key",
    tags="production",
    page_size=50
)

for secret in api_secrets['results']:
    print(f"{secret['key']}: {secret['secret_type']}")
```

#### Get Secret (with 2-Tier Inheritance)

```python
# Get secret (simple)
secret = client.secrets.get_secret("DATABASE_URL")
print(secret['value'])

# Get with app context (2-tier inheritance: app-level → site-level)
prod_secret = client.secrets.get_secret(
    "DATABASE_URL",
    app="production"
)

# Get with tag validation
secret = client.secrets.get_secret(
    "STRIPE_KEY",
    tags=["payment", "production"]
)
```

#### Batch Get Secrets (Concurrent)

```python
# Get multiple secrets at once
keys = ["API_KEY", "DATABASE_URL", "STRIPE_KEY"]
secrets = client.secrets.get_secrets(keys)

# Returns: {"API_KEY": {...}, "DATABASE_URL": {...}, "STRIPE_KEY": {...}}
for key, secret in secrets.items():
    print(f"{key}: {secret['secret_type']}")

# With app context
prod_secrets = client.secrets.get_secrets(
    ["API_KEY", "DATABASE_URL"],
    app="production"
)
```

#### Update Secret

```python
# Update secret value
updated = client.secrets.update("API_KEY", value="new_value_here")
```

---

### Policy & Authorization

#### Check Permissions (Cerbos Integration)

```python
# Check if user can perform actions on resources
result = client.policy.check_resources(
    principal={
        "id": "user123",
        "roles": ["editor", "reviewer"]
    },
    resources=[
        {
            "kind": "document",
            "id": "doc1",
            "attr": {"owner": "user123", "status": "draft"}
        }
    ],
    actions=["view", "edit", "delete"]
)

# Returns: {"doc1": {"view": True, "edit": True, "delete": False}}
for resource_id, actions in result.items():
    print(f"{resource_id}: {actions}")
```

#### Filter Allowed Resources

```python
# Get only resources where specific actions are allowed
allowed = client.policy.filter_allowed(
    principal={"id": "user123", "roles": ["editor"]},
    resources=[...],  # List of resources
    actions=["edit"]
)
# Returns only resources where user can "edit"
```

#### Get Allowed Actions

```python
# Get all actions user can perform on a resource
actions = client.policy.get_allowed_actions(
    principal={"id": "user123", "roles": ["editor"]},
    resource={
        "kind": "document",
        "id": "doc1",
        "attr": {"owner": "user123"}
    },
    actions=["view", "edit", "delete", "publish"]
)
# Returns: ["view", "edit"]
```

---

### Analytics

Execute pre-configured analytics queries to retrieve insights and metrics from your application.

#### Execute Analytics Query

```python
# Execute analytics query
result = client.analytics.execute(
    "monthly-revenue",
    params={
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    }
)
print(result["data"])
```

#### Query with Grouping

```python
# Group results by month
result = client.analytics.execute(
    "user-signups",
    params={
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "group_by": "month"
    }
)

# Results grouped by month
for month_data in result["data"]:
    print(f"{month_data['month']}: {month_data['count']} signups")
```

#### Query with Filters

```python
# Execute query with custom filters
result = client.analytics.execute(
    "sales-by-region",
    params={
        "region": "US",
        "product_category": "electronics",
        "start_date": "2024-Q1"
    }
)

# Access filtered data
print(f"Total sales: {result['data']['total']}")
print(f"Average: {result['data']['average']}")
```

---

### App & Settings

#### Get App Roles

```python
# Get roles defined in the app
roles = client.app.roles()
print(roles)  # ["admin", "editor", "viewer"]
```

#### Get Site Settings

```python
# Get site metadata/settings
settings = client.settings.get()
print(settings['site_name'])
print(settings['settings'])
```

---

## Async vs Sync

### When to Use Async

Use **async mode** (`mode='async'`) when:
- Building async applications (FastAPI, aiohttp, etc.)
- Need true concurrency for I/O-bound operations
- Making many parallel requests
- Working in async event loops

```python
client = Client(
    mode='async',
    api_url="https://api.taruvi.cloud",
    app_slug="my-app"
)
auth_client = client.auth.signInWithToken(token="jwt_here", token_type="jwt")

# All methods are async
result = await auth_client.functions.execute("my-func", params={})
users = await auth_client.database.query("users").get()
```

### When to Use Sync

Use **sync mode** (`mode='sync'` or default) when:
- Writing scripts, CLIs, or standalone applications
- Running in Jupyter notebooks
- Inside Taruvi function handlers
- Simplicity is preferred over concurrency
- You're NOT in an async event loop

```python
# mode='sync' is default
client = Client(
    api_url="https://api.taruvi.cloud",
    app_slug="my-app"
)
auth_client = client.auth.signInWithToken(token="jwt_here", token_type="jwt")

# All methods are blocking (no await)
result = auth_client.functions.execute("my-func", params={})
users = auth_client.database.query("users").get()
```

### Performance Note

The sync client uses **native `httpx.Client` (blocking)** - NOT `asyncio.run()` wrapper.

**Benefits:**
- ✅ 10-50x faster than asyncio wrappers for high-frequency usage
- ✅ Thread-safe and works in any Python environment
- ✅ Compatible with Jupyter notebooks, FastAPI apps, anywhere
- ✅ No event loop conflicts

---

## Configuration

### Client Initialization Parameters

```python
client = Client(
    # Mandatory
    api_url="https://api.taruvi.cloud",  # Taruvi API base URL
    app_slug="my-app",                    # Application slug

    # Optional: Mode
    mode='sync',  # 'sync' (default) or 'async'

    # Optional: Configuration
    timeout=30,       # Request timeout (seconds, 1-300, default: 30)
    max_retries=3,    # Max retry attempts (0-10, default: 3)

    # Optional: Multi-tenant routing
    site_slug="my-site",  # Site slug for multi-tenant routing
)

# Authentication is done separately via AuthManager
auth_client = client.auth.signInWithPassword(username="...", password="...")
```

### Configuration Table

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_url` | `str` | **Required** | Taruvi API base URL |
| `app_slug` | `str` | **Required** | Application slug |
| `mode` | `str` | `'sync'` | Client mode: `'sync'` or `'async'` |
| `timeout` | `int` | `30` | Request timeout in seconds (1-300) |
| `max_retries` | `int` | `3` | Maximum retry attempts (0-10) |
| `site_slug` | `str` | `None` | Site slug for multi-tenant routing |

**Note**: Authentication parameters are no longer passed to `Client()`. Use `AuthManager` methods instead.

### Environment Variables

Configuration parameters can be set via environment variables with `TARUVI_` prefix:

```bash
# Client configuration
TARUVI_API_URL=https://api.taruvi.cloud
TARUVI_APP_SLUG=my-app
TARUVI_MODE=sync
TARUVI_TIMEOUT=60
TARUVI_MAX_RETRIES=5
TARUVI_SITE_SLUG=my-site

# Authentication credentials (use with AuthManager)
TARUVI_JWT=your_jwt_token
TARUVI_API_KEY=your_api_key
TARUVI_SESSION_TOKEN=your_session_token
TARUVI_USERNAME=alice@example.com
TARUVI_PASSWORD=secret123
```

Load them in your code:

```python
import os
from taruvi import Client

client = Client(
    api_url=os.getenv("TARUVI_API_URL"),
    app_slug=os.getenv("TARUVI_APP_SLUG")
)

# Authenticate
auth_client = client.auth.signInWithPassword(
    username=os.getenv("TARUVI_USERNAME"),
    password=os.getenv("TARUVI_PASSWORD")
)
```

### Context Managers

```python
# Sync client
client = Client(api_url="...", app_slug="...")
auth_client = client.auth.signInWithPassword(username="...", password="...")

with auth_client as client:
    result = client.functions.execute("my-func", params={})
# Automatically closes connection

# Async client
client = Client(mode='async', api_url="...", app_slug="...")
auth_client = client.auth.signInWithPassword(username="...", password="...")

async with auth_client as client:
    result = await client.functions.execute("my-func", params={})
# Automatically closes connection
```

---

## Error Handling

### Exception Hierarchy

All exceptions inherit from `TaruviError`:

```
TaruviError (base)
├── ConfigurationError      # Invalid/missing configuration
├── APIError (base)
│   ├── ValidationError           # 400 Bad Request
│   ├── AuthenticationError       # 401 Unauthorized
│   ├── NotAuthenticatedError     # 401 No credentials
│   ├── AuthorizationError        # 403 Forbidden
│   ├── NotFoundError             # 404 Not Found
│   ├── ConflictError             # 409 Conflict
│   ├── RateLimitError            # 429 Too Many Requests
│   ├── ServerError               # 500 Internal Server Error
│   └── ServiceUnavailableError   # 503 Service Unavailable
├── NetworkError (base)
│   ├── TimeoutError        # Request timeout
│   └── ConnectionError     # Connection failure
├── RuntimeError            # SDK runtime errors
│   └── FunctionExecutionError  # Function execution failures
└── ResponseError           # Response parsing failures
```

### Handling Errors

```python
from taruvi import (
    Client,
    ValidationError,
    AuthenticationError,
    NotFoundError,
    TimeoutError,
    TaruviError
)

# Create and authenticate client
client = Client(api_url="...", app_slug="...")
auth_client = client.auth.signInWithPassword(username="...", password="...")

try:
    user = auth_client.database.get("users", record_id=123)
except ValidationError as e:
    print(f"Invalid request: {e.message}")
    print(f"Details: {e.details}")
except AuthenticationError as e:
    print(f"Auth failed: {e.message}")
except NotFoundError as e:
    print(f"User not found: {e.message}")
except TimeoutError as e:
    print(f"Request timed out: {e.message}")
except TaruviError as e:
    # Catch all Taruvi errors
    print(f"Taruvi error [{e.status_code}]: {e.message}")
    print(f"Details: {e.to_dict()}")
```

### Exception Properties

```python
try:
    result = client.functions.execute("my-func", params={})
except TaruviError as e:
    print(e.message)        # Error message
    print(e.status_code)    # HTTP status code (if applicable)
    print(e.details)        # Additional error details (dict)
    print(e.to_dict())      # Convert to dictionary
```

### Retry Behavior

The SDK automatically retries failed requests with exponential backoff:

- **Default retries**: 3 attempts
- **Retried status codes**: 429 (Rate Limit), 500 (Server Error), 503 (Service Unavailable)
- **Backoff formula**: `2^attempt` seconds (1s, 2s, 4s, ...)
- **Configurable**: Set `max_retries` parameter

```python
# Disable retries
client = Client(
    api_url="...",
    app_slug="...",
    max_retries=0  # No retries
)
auth_client = client.auth.signInWithPassword(username="...", password="...")

# More aggressive retries
client = Client(
    api_url="...",
    app_slug="...",
    max_retries=5,   # Try 5 times
    timeout=60        # Wait longer
)
auth_client = client.auth.signInWithPassword(username="...", password="...")
```

---

## Advanced Usage

### Custom Timeouts

```python
# Global timeout (all requests)
client = Client(
    api_url="...",
    app_slug="...",
    timeout=60  # 60 seconds
)
auth_client = client.auth.signInWithPassword(username="...", password="...")

# Per-request timeout (functions only)
result = auth_client.functions.execute(
    "long-task",
    params={},
    timeout=120  # Override for this request
)
```

### Connection Pooling

The SDK uses connection pooling by default:

- **Max connections**: 10 concurrent connections
- **Keep-alive**: Enabled
- **SSL verification**: Always enabled
- **Redirect following**: Enabled

This is handled automatically by `httpx` - no configuration needed.

### Runtime Detection

The SDK auto-detects when running inside Taruvi functions:

```python
from taruvi import detect_runtime, is_inside_function, RuntimeMode

# Check runtime mode
mode = detect_runtime()
print(mode)  # RuntimeMode.FUNCTION or RuntimeMode.EXTERNAL

# Check if inside function
if is_inside_function():
    print("Running inside Taruvi function!")

# Get function context
from taruvi import get_function_context
context = get_function_context()
print(context['function_id'])
print(context['execution_id'])
```

### Multi-Tenant Routing

For multi-tenant setups, specify the site:

```python
client = Client(
    api_url="https://api.taruvi.cloud",
    app_slug="my-app",
    site_slug="tenant-a"  # Routes to tenant-a's schema
)
auth_client = client.auth.signInWithToken(token="jwt_here", token_type="jwt")
```

Sends header: `Host: tenant-a.localhost`

### Working with Raw Responses

All SDK methods return `dict[str, Any]` - plain dictionaries:

```python
# Create and authenticate
client = Client(api_url="...", app_slug="...")
auth_client = client.auth.signInWithPassword(username="...", password="...")

# No complex model classes - just dicts
result = auth_client.functions.execute("my-func", params={})
print(type(result))  # <class 'dict'>

# Access like normal dict
print(result['data'])
print(result.get('invocation', {}))

# Full IDE autocomplete via type hints
users: list[dict[str, Any]] = auth_client.database.query("users").get()
```

---

## Development

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/taruvi/taruvi-python-sdk.git
cd taruvi-python-sdk

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Or with Poetry
poetry install --with dev
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/taruvi --cov-report=html

# Run specific test file
pytest tests/test_database_integration.py -v

# Run integration tests (requires backend)
RUN_INTEGRATION_TESTS=1 pytest tests/ -v
```

### Code Quality

```bash
# Format code with Black
black src/ tests/

# Lint with Ruff
ruff check src/ tests/

# Type checking with mypy
mypy src/taruvi
```

### Project Structure

```
taruvi-python-sdk/
├── src/taruvi/
│   ├── __init__.py           # Public API exports
│   ├── client.py             # Async client & factory
│   ├── sync_client.py        # Sync client
│   ├── config.py             # Configuration
│   ├── auth.py               # Auth manager
│   ├── exceptions.py         # Exception hierarchy
│   ├── http_client.py        # Async HTTP client
│   ├── sync_http_client.py   # Sync HTTP client
│   ├── runtime.py            # Runtime detection
│   └── modules/              # API modules
│       ├── functions.py
│       ├── database.py
│       ├── auth.py
│       ├── storage.py
│       ├── secrets.py
│       ├── policy.py
│       ├── app.py
│       └── settings.py
├── tests/                    # Test suite
├── examples/                 # Usage examples
├── pyproject.toml           # Project configuration
├── LICENSE                  # MIT License
└── README.md               # This file
```

---

## Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository** on GitHub
2. **Create a feature branch**: `git checkout -b feature/my-feature`
3. **Make your changes** with tests
4. **Run tests and linting**: `pytest && black . && ruff check .`
5. **Commit your changes**: `git commit -m "Add my feature"`
6. **Push to your fork**: `git push origin feature/my-feature`
7. **Open a Pull Request** on GitHub

### Code Guidelines

- **Type hints**: All functions must have complete type annotations
- **Tests**: New features must include tests
- **Documentation**: Update docstrings and README
- **Code style**: Follow Black formatting (100 char line length)
- **Commits**: Use clear, descriptive commit messages

### Reporting Issues

Found a bug? Have a feature request?

- **Issues**: [GitHub Issues](https://github.com/taruvi/taruvi-python-sdk/issues)
- **Security**: Email security@taruvi.cloud (do not open public issues)

---

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 Taruvi Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

## Support

Need help? We're here for you:

📚 **Documentation**: [docs.taruvi.cloud](https://docs.taruvi.cloud)
🐛 **Issues**: [GitHub Issues](https://github.com/taruvi/taruvi-python-sdk/issues)
💬 **Community**: [Taruvi Discord](https://discord.gg/taruvi)
📧 **Email**: support@taruvi.cloud
🌐 **Website**: [taruvi.cloud](https://taruvi.cloud)

---

## Related Projects

- **[Taruvi JavaScript SDK](https://github.com/taruvi/taruvi-js-sdk)** - Official JS/TS SDK
- **[Taruvi CLI](https://github.com/taruvi/taruvi-cli)** - Command-line interface
- **[Taruvi Examples](https://github.com/taruvi/examples)** - Example applications

---

<p align="center">
  Made with ❤️ by the <a href="https://taruvi.cloud">Taruvi Team</a>
</p>

<p align="center">
  <a href="https://taruvi.cloud">Website</a> •
  <a href="https://docs.taruvi.cloud">Documentation</a> •
  <a href="https://github.com/taruvi">GitHub</a> •
  <a href="https://twitter.com/taruvi">Twitter</a>
</p>
