# Changelog

All notable changes to the Taruvi Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.2b1] - 2026-09-28

Pre-release of 0.2.2 for beta testing. Install it with `pip install --pre taruvi` or `pip install taruvi==0.2.2b1`.

### Added
- Every request identifies the SDK with `X-Taruvi-Client` and `User-Agent` headers, for example `taruvi-python/0.2.2 (python/3.12.4)`, so the platform can tell which SDK and version made a call.
- `GatewayTimeoutError` for `504 Gateway Timeout` responses (query and upstream timeouts).
- `BillingError` for billing-gate refusals: `402 account_suspended`, `429 product_suspended`, and `503 gate_unavailable`, with `module` and `retryable`. These were `APIError`, `RateLimitError`, and `ServiceUnavailableError`.
- Every API error now carries the platform error envelope: `error.code` (for example `"NOT_FOUND"`) and `error.detail`.

### Changed
- `functions.execute()` now omits `async` unless you pass `is_async`, so the function's own default execution mode applies. Pass `is_async=False` to keep forcing a synchronous run.
- A credential passed to `Client()` (`api_key`, `jwt`, or `session_token`) now replaces every credential in the environment, and each request sends exactly one credential. Previously `Client(session_token=...)` also sent `TARUVI_API_KEY` from the environment, and data-table requests then ran as the key's owner instead of the user.
- `NotAuthenticatedError` is now a subclass of `AuthenticationError`.

### Fixed
- Timeouts and dropped connections no longer resend `POST` or `PATCH` requests the server may already have applied, such as record creates and function runs. They are still retried when the connection never opened; `GET`, `PUT`, and `DELETE` keep their retries.
- `functions.execute(timeout=...)` was ignored; it now sets that call's timeout.
- `storage.upload()` sent every file as `application/octet-stream`, so TaruviBase stored that MIME type; it now guesses the type from the filename, or takes `(filename, file, content_type)`. It returns the batch result (`uploaded_count`, `successful`, `failed`) and raises SDK errors instead of `httpx.HTTPStatusError`.
- `storage.download()` returned the error body as file bytes on `403` or `404`; it now raises the matching SDK error.
- `storage.upload()` and `storage.download()` raised raw `httpx` exceptions on network failures; they now raise `TimeoutError` or `ConnectionError`. A dropped connection (`RemoteProtocolError`) is now handled like other network errors.
- `count()` downloaded every matching record; it now requests one row and reads the total.
- A filter tree (`filter({...})`) replaced the flat filters on the same query, so reads returned, and `delete_filtered()` deleted, rows matching the tree alone. Both are now sent and combined with AND.
- `storage.delete()` returns the batch result (`deleted_count`, `failed`) instead of `None`, so skipped objects, such as those a policy denies, are visible.
- A trailing slash on `api_url` produced `//api/...` storage URLs; it is now removed.
- Object paths are URL-encoded segment by segment, so names containing spaces, `#`, or `?` reach the right object.
- `taruvi.__version__` reports the installed package version instead of `0.1.9`.
- Error messages fall back to the response's `detail` when it has no `message`, instead of the raw response body.
- Errors for HTTP statuses without a dedicated class (for example 422 or 502) kept `details` in `status_code`; they now carry the real status code.
- `delete_filtered()` with a filter tree sent a value the delete endpoint rejects; the tree is now sent under `filters`, matching list requests.
- `delete_filtered()` with no filters now raises `ValueError` before sending a request.
- Docstrings showed `client.database.query(...)`, `signInWithPassword(username=...)`, and a no-argument `Client()`; they now show `from_(...)`, `email=`, and the `sdk_client` passed to function code.
- `delete_filtered()` raises `ValueError` when the query also uses `search()`, `vector_search()`, `page()`, `page_size()`, or aggregation, instead of dropping them and deleting every row that matches the other filters.
- `first()` returned the wrong row when `page()` was set; it now reads the requested page, and no longer changes the builder's page size.
- The `Secret` type hint now declares `value` and `tags`, which `secrets.get()` returns.
- Docstring examples for `auth.get_current_user()`, `secrets.list()`, and `users.list()` read the fields the platform actually returns (`["data"]`), and no longer call a nonexistent `list_secrets()`.

### Deprecated
- The `principal` argument of the policy methods. The platform rejects an explicit principal with a 400; checks always run as the authenticated caller.

## [0.1.6] - 2026-03-26

### Added
- **Database: Full-text search** via `.search(query)` on QueryBuilder
  - Translates to PostgreSQL `tsvector` search on tables with `search_vector` field
- **Database: Aggregation support** via `.aggregate()`, `.group_by()`, `.having()` on QueryBuilder
- **Database: Edge CRUD via QueryBuilder** — chainable `.edges()` toggle
  - `client.database.from_("table").edges().create([...]).execute()`
  - `client.database.from_("table").edges().get(id).update({...}).execute()`
  - `client.database.from_("table").edges().delete([ids]).execute()`
  - Replaces standalone `list_edges`, `create_edges`, `delete_edges`, `update_edge` methods
- **Database: Lazy CRUD on QueryBuilder** — `.get(id)`, `.create(body)`, `.update(body)`, `.delete(id)` are now chainable and execute lazily via `.execute()`
- **App settings endpoint** — `client.app.settings()` returns app display_name, colors, icon, category, URLs, etc.
- **User attributes endpoint** — new `_USER_ATTRIBUTES` path in settings module
- New test suites: aggregations (sync + async), app settings integration, database edges, database search, live edge tests

### Changed
- **BREAKING: `users.create()` signature** — now accepts a single `data: dict` instead of individual keyword arguments
  ```python
  # Before
  client.users.create(username="alice", email="alice@example.com", password="...", confirm_password="...")

  # After
  client.users.create({"username": "alice", "email": "alice@example.com", "password": "...", "confirm_password": "..."})
  ```
- **BREAKING: `users.update()` signature** — now accepts `(username, data: dict)` instead of individual keyword arguments
  ```python
  # Before
  client.users.update(username="alice", email="new@example.com", is_active=False)

  # After
  client.users.update("alice", {"email": "new@example.com", "is_active": False})
  ```
- **BREAKING: `secrets.list()` response format** — now returns the full API response `{"status", "message", "data", "total"}` instead of extracting data
- **Database sorting** — now uses `ordering` parameter (`-field` for desc) instead of separate `_sort`/`_order` params
- **AuthModule** now extends `BaseModule` for consistent inheritance
- Removed `_parse_user_apps` helper in users module; uses `_extract_data_list` instead
- Trimmed verbose docstrings across database module methods

### Fixed
- Delete edge API path handling
- Sort ordering in database queries

## [0.1.3] - 2026-02-18

### Changed
- **BREAKING**: Simplified Users module method names to remove redundant suffixes
  - `get_user` → `get`
  - `create_user` → `create`
  - `update_user` → `update`
  - `delete_user` → `delete`
  - `list_users` → `list`
  - `get_user_apps` → `apps`
- **BREAKING**: Secrets module now uses a single `list()` method
  - Batch retrieval is now `list(keys=[...])`
  - `get_many` removed
- Documentation and tests updated for the new method names

### Added
- **Unified Client API** with `mode` parameter
  - `Client(mode='sync')` - Native blocking client (default)
  - `Client(mode='async')` - Async client for async frameworks
  - Single import, consistent API across both modes
- **Additional API modules**
  - Storage API for file/object storage operations
  - Secrets API for secure credential management
  - Policy API for Cerbos policy checks
  - App API for role and user management
  - Settings API for site configuration
- **TaruviConfig.from_runtime_and_params()** factory method
  - Consistent configuration merging for both async and sync clients
  - Leverages Pydantic's built-in field precedence
  - Simplified client initialization

### Changed
- **REFACTOR**: Native blocking implementation for sync mode
  - Uses `httpx.Client` (blocking) instead of `asyncio.run()` wrapper
  - 10-50x performance improvement for high-frequency usage
  - Eliminates event loop creation overhead (~10-50ms per call)
  - Now thread-safe and works in all Python environments
  - Compatible with Jupyter notebooks, FastAPI apps, and any async context
  - No longer crashes with `RuntimeError: asyncio.run() cannot be called from a running event loop`
- **Unified module structure** - Single set of modules work for both sync/async
  - Removed separate `sync_*` module files
  - Cleaner codebase with shared implementation logic
- **Config merging** now uses factory method
  - Runtime detection handled internally
  - Consistent merge logic between sync and async clients

### Internal
- Refactored to internal `_AsyncClient` and `_SyncClient` classes
- Public `Client()` factory function for mode selection
- Improved type hints with `@overload` decorators
- Comprehensive test suite added

### Migration Notes
- **No breaking changes** - Public API remains identical
- Module methods work exactly the same way (still return `dict[str, Any]`)
- Internal implementation improved for better performance
- Users will experience performance improvements automatically

## [1.3.0] - 2026-01-19

### Changed
- Updated `get_secrets()` method to use `GET /api/secrets/?keys=...` instead of `POST /api/secrets/batch/`
- Improved RESTful compliance - batch retrieval now uses GET request with query parameters
- More cacheable and follows HTTP semantic conventions

### Migration Guide
**No code changes required** - the method signature remains identical. Existing code continues to work:

```python
# Your existing code works unchanged
secrets = client.secrets.get_secrets(["key1", "key2", "key3"])
```

**Technical Details:**
- Changed HTTP method from POST to GET
- Changed endpoint from `/api/secrets/batch/` to `/api/secrets/`
- Changed payload format from JSON body to query parameters
- Keys are now passed as comma-separated string: `keys=key1,key2,key3`

**Notes:**
- Backend API maintains backward compatibility during deprecation period
- Older SDK versions will stop working after backend removes POST endpoint
- Recommended to upgrade to v1.3.0+ before backend deprecation ends

## [0.1.0] - 2025-12-26

### Added
- Initial release of Taruvi Python SDK
- Dual-mode operation: external applications and function runtime
- Async `Client` for external applications
- Sync `SyncClient` for use inside Taruvi functions
- Auto-configuration when running inside functions
- Runtime detection utilities
- Functions API module
- Database API module with QueryBuilder
- Auth API module
- HTTP client with retry logic and exponential backoff
- Connection pooling
- Comprehensive exception hierarchy
- Type hints throughout the codebase
- Full documentation and examples

### Security
- Function-scoped JWT token generation
- RestrictedPython sandbox support
- Thread-local storage for client isolation

[Unreleased]: https://github.com/taruvi-ai/taruvi-python-sdk/compare/v0.1.6...HEAD
[0.1.6]: https://github.com/taruvi-ai/taruvi-python-sdk/compare/v0.1.3...v0.1.6
[0.1.3]: https://github.com/taruvi-ai/taruvi-python-sdk/compare/v1.3.0...v0.1.3
[1.3.0]: https://github.com/taruvi-ai/taruvi-python-sdk/compare/v0.1.0...v1.3.0
[0.1.0]: https://github.com/taruvi-ai/taruvi-python-sdk/releases/tag/v0.1.0
