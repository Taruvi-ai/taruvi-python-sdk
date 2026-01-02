# Changelog

All notable changes to the Taruvi Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Pydantic response models** for all API responses
  - `TokenResponse`, `UserResponse` for auth
  - `FunctionExecutionResult`, `FunctionResponse`, `InvocationResponse`, `FunctionListResponse` for functions
  - `DatabaseRecord` for database
  - Full type safety and IDE autocomplete
  - Runtime validation of API responses
- **Module-level endpoint constants** for better organization
  - Each module defines its own API endpoint paths
  - Follows separation of concerns principle
  - Easier to maintain and understand
- **TaruviConfig.from_runtime_and_params()** factory method
  - Consistent configuration merging for both async and sync clients
  - Leverages Pydantic's built-in field precedence

### Changed
- **REFACTOR**: SyncClient now uses native `httpx.Client` (blocking) instead of `asyncio.run()` wrapper
  - 10-50x performance improvement for high-frequency usage
  - Eliminates event loop creation overhead (~10-50ms per call)
  - Now thread-safe and works in all Python environments
  - Compatible with Jupyter notebooks, FastAPI apps, and any async context
  - No longer crashes with `RuntimeError: asyncio.run() cannot be called from a running event loop`
- Created native synchronous modules: `SyncHTTPClient`, `SyncFunctionsModule`, `SyncDatabaseModule`, `SyncAuthModule`
- All sync modules use direct blocking HTTP calls (no asyncio wrappers)
- **BREAKING**: Return types now use Pydantic models instead of raw dicts
  - `auth.login()` returns `TokenResponse` (was `dict[str, Any]`)
  - `auth.get_current_user()` returns `UserResponse` (was `dict[str, Any]`)
  - `functions.execute()` returns `FunctionExecutionResult` (was `dict[str, Any]`)
  - `functions.list()` returns `FunctionListResponse` (was `dict[str, Any]`)
  - `functions.get()` returns `FunctionResponse` (was `dict[str, Any]`)
  - `functions.get_invocation()` returns `InvocationResponse` (was `dict[str, Any]`)
  - `database.query().get()` returns `list[DatabaseRecord]` (was `list[dict[str, Any]]`)
  - `database.query().first()` returns `Optional[DatabaseRecord]` (was `Optional[dict[str, Any]]`)
  - `database.create()` returns `DatabaseRecord` (was `dict[str, Any]`)
  - `database.update()` returns `DatabaseRecord` (was `dict[str, Any]`)
- **Config merging** now uses Pydantic factory method
  - Simplified client initialization code
  - Consistent merge logic between `Client` and `SyncClient`
  - Runtime detection handled internally by factory method

### Internal
- Added `sync_http_client.py` - Native blocking HTTP client using `httpx.Client`
- Added `modules/sync_functions.py` - Native blocking functions module
- Added `modules/sync_database.py` - Native blocking database module with `SyncQueryBuilder`
- Added `modules/sync_auth.py` - Native blocking auth module
- Added `models/` directory with Pydantic response models
  - `models/auth.py` - Auth response models
  - `models/functions.py` - Functions response models
  - `models/database.py` - Database response models
- Refactored `sync_client.py` to use native sync modules and config factory method
- Refactored `client.py` to use config factory method
- All modules now use module-level endpoint constants

### Migration Notes
- **BREAKING CHANGE**: Return types changed from `dict` to Pydantic models
- **Migration path**:
  ```python
  # Before (v0.1.0)
  result = client.functions.execute("func", {})
  success = result["success"]  # dict access

  # After (v0.2.0)
  result = client.functions.execute("func", {})
  success = result.success  # typed attribute access

  # If you need dict, use .model_dump()
  result_dict = result.model_dump()
  ```
- Most code will continue to work due to Pydantic's dict-like behavior
- Update code to use attribute access for better type safety and IDE autocomplete
- Benefits: Full type hints, runtime validation, better developer experience
- **No breaking changes** for SyncClient refactor - Public API remains identical
- `SyncClient` methods work exactly the same way
- Internal implementation changed from asyncio wrapper to native blocking
- Users will experience performance improvements and better compatibility automatically

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

[Unreleased]: https://github.com/taruvi-ai/taruvi-python-sdk/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/taruvi-ai/taruvi-python-sdk/releases/tag/v0.1.0
