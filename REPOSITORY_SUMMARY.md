# Taruvi Python SDK - Repository Summary

## Overview

The Taruvi Python SDK is now maintained as a **separate, standalone repository** independent from the main Taruvi platform.

**Repository Location:**
- **Local**: `/home/neha/Projects/Taruvi_new/taruvi-python-sdk`
- **GitHub**: `https://github.com/taruvi-ai/taruvi-python-sdk` (to be created)

---

## Repository Structure

```
taruvi-python-sdk/
├── .github/
│   └── workflows/
│       └── ci.yml                  # CI/CD pipeline (pytest, black, ruff, mypy)
│
├── src/
│   └── taruvi/                     # SDK source code
│       ├── __init__.py             # Public API exports
│       ├── client.py               # Async Client
│       ├── sync_client.py          # Sync Client wrapper
│       ├── config.py               # Configuration & runtime detection
│       ├── exceptions.py           # Exception hierarchy
│       ├── http_client.py          # HTTP client with retry logic
│       ├── runtime.py              # Runtime detection utilities
│       └── modules/
│           ├── __init__.py
│           ├── functions.py        # Functions API
│           ├── database.py         # Database API with QueryBuilder
│           └── auth.py             # Authentication API
│
├── tests/                          # Test files (to be added)
│   └── __init__.py
│
├── .gitignore                      # Python .gitignore
├── CHANGELOG.md                    # Version history
├── CONTRIBUTING.md                 # Contribution guidelines
├── LICENSE                         # MIT License
├── README.md                       # Main documentation
├── pyproject.toml                  # Package configuration
├── SETUP_GUIDE.md                  # Setup and publishing guide
└── REPOSITORY_SUMMARY.md           # This file
```

---

## Key Files

### Package Configuration

**pyproject.toml**
- Package name: `taruvi`
- Version: `0.1.0`
- Python: `>=3.10`
- Dependencies: `httpx`, `pydantic`, `pydantic-settings`, `python-dotenv`
- Build system: `hatchling`

### Documentation

1. **README.md** - Complete SDK documentation
   - Installation instructions
   - Quick start examples
   - API reference
   - Error handling
   - Configuration options

2. **SETUP_GUIDE.md** - Repository setup
   - Git initialization
   - GitHub setup
   - Publishing to PyPI
   - CI/CD configuration
   - Platform integration

3. **CONTRIBUTING.md** - Development guidelines
   - Development setup
   - Code formatting (black)
   - Linting (ruff)
   - Type checking (mypy)
   - Testing (pytest)
   - Pull request process

4. **CHANGELOG.md** - Version history
   - Tracks all changes
   - Follows Keep a Changelog format
   - Semantic versioning

### CI/CD

**.github/workflows/ci.yml**
- Runs on: `push` and `pull_request`
- Python versions: 3.10, 3.11, 3.12
- Checks:
  - Linting (ruff)
  - Formatting (black)
  - Type checking (mypy)
  - Tests (pytest)
  - Coverage (codecov)
  - Package build

---

## SDK Features

### Dual-Mode Operation

**Mode 1: External Applications**
```python
from taruvi import Client

client = Client(
    api_url="http://localhost:8000",
    api_key="jwt_token",
    site_slug="site-slug"
)

result = await client.functions.execute("func", {...})
```

**Mode 2: Inside Taruvi Functions**
```python
# No imports or configuration needed!
def main(params, user_data):
    # 'client' is automatically available as global
    result = client.functions.execute("other-func", {...})
    return result
```

### Core Components

1. **Client** - Async client for external apps
2. **SyncClient** - Sync client for functions
3. **Runtime Detection** - Auto-detect execution environment
4. **HTTP Client** - Retry logic, connection pooling
5. **Exceptions** - Comprehensive error hierarchy
6. **API Modules**:
   - Functions API
   - Database API (with QueryBuilder)
   - Auth API

---

## Platform Integration

The Taruvi platform has been updated to work with the separate SDK:

### Modified Platform Files

**cloud_site/functions/client_factory.py** (NEW)
- Creates SDK clients in Celery workers
- Generates function-scoped JWT tokens
- Thread-local storage for client isolation

**cloud_site/functions/tasks.py**
- Injects SDK environment variables
- Creates SDK client via factory
- Cleans up after execution

**cloud_site/functions/providers/app.py**
- Retrieves client from thread-local storage
- Injects client as global `client` variable
- Available in user function namespace

### Platform Installation

Install SDK in platform:

```bash
# Development (editable install)
pip install -e /home/neha/Projects/Taruvi_new/taruvi-python-sdk

# Production (from GitHub)
pip install git+https://github.com/taruvi-ai/taruvi-python-sdk.git@main

# Future (from PyPI)
pip install taruvi
```

---

## Development Workflow

### Working on SDK

```bash
cd /home/neha/Projects/Taruvi_new/taruvi-python-sdk

# Make changes
vim src/taruvi/client.py

# Test
pytest

# Format
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/

# Commit and push
git add .
git commit -m "Add: new feature"
git push
```

### Testing with Platform

```bash
# Platform automatically picks up changes (editable install)
cd /home/neha/Projects/Taruvi_new/Taruvi

# Restart services to test
python manage.py runserver
# Or: docker-compose restart
```

---

## Publishing

### Version Update

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Commit changes
4. Create git tag

```bash
# Update version
vim pyproject.toml  # Change version = "0.2.0"

# Update changelog
vim CHANGELOG.md

# Commit
git add .
git commit -m "Release: version 0.2.0"

# Tag
git tag -a v0.2.0 -m "Release version 0.2.0"
git push origin v0.2.0
```

### Publish to PyPI

```bash
# Build
python -m build

# Test on TestPyPI
twine upload --repository testpypi dist/*

# Publish to PyPI
twine upload dist/*
```

---

## Testing

### SDK Tests

```bash
cd /home/neha/Projects/Taruvi_new/taruvi-python-sdk

# Run all tests
pytest

# Run with coverage
pytest --cov=taruvi --cov-report=html

# Run specific test
pytest tests/test_client.py -v
```

### Integration Tests

Test SDK in platform:

```bash
cd /home/neha/Projects/Taruvi_new/Taruvi

# Django shell test
python manage.py shell
>>> from taruvi import Client
>>> print("✅ SDK imported!")

# Function execution test
# Upload example_sdk_function.py
# Execute via API
# Verify 'client' is available in function
```

---

## Next Steps

### Immediate

1. ✅ SDK extracted to separate repository
2. ✅ Repository structure created
3. ✅ Documentation added
4. ✅ CI/CD configured
5. ⬜ Push to GitHub
6. ⬜ Add comprehensive tests
7. ⬜ Set up Codecov

### Future

1. ⬜ Publish to PyPI
2. ⬜ Add more API modules (Storage, Events)
3. ⬜ Add Sphinx documentation
4. ⬜ Create video tutorials
5. ⬜ Add example projects

---

## Advantages of Separate Repository

### For SDK

✅ **Independent versioning** - SDK has its own release cycle
✅ **Easier distribution** - Can be published to PyPI
✅ **Better organization** - SDK code separated from platform
✅ **Dedicated CI/CD** - SDK-specific testing and validation
✅ **Community contributions** - Easier for external contributors
✅ **Cleaner structure** - No mixing of client and server code

### For Platform

✅ **Cleaner codebase** - Platform doesn't contain client library
✅ **Flexible installation** - Install from PyPI, Git, or local
✅ **Easier updates** - Update SDK version independently
✅ **Better testing** - Test SDK separately from platform
✅ **Version pinning** - Lock to specific SDK version

---

## Support

### SDK Issues
- **Repository**: `/home/neha/Projects/Taruvi_new/taruvi-python-sdk`
- **GitHub Issues**: (to be created)
- **Documentation**: `README.md`

### Platform Integration
- **Guide**: `/home/neha/Projects/Taruvi_new/Taruvi/SDK_INSTALLATION.md`
- **Factory**: `cloud_site/functions/client_factory.py`
- **Tasks**: `cloud_site/functions/tasks.py`

---

## Status

- **SDK Status**: ✅ Fully implemented and working
- **Repository Status**: ✅ Extracted to separate location
- **Documentation**: ✅ Complete
- **CI/CD**: ✅ Configured
- **GitHub**: ⬜ To be pushed
- **PyPI**: ⬜ To be published

---

**Created**: 2025-12-26
**SDK Version**: 0.1.0
**Python**: >=3.10
**License**: MIT
