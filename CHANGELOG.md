# Changelog

All notable changes to the Taruvi Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/taruvi-ai/taruvi-python-sdk/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/taruvi-ai/taruvi-python-sdk/compare/v0.1.0...v1.3.0
[0.1.0]: https://github.com/taruvi-ai/taruvi-python-sdk/releases/tag/v0.1.0
