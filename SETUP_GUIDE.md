# Taruvi Python SDK - Setup Guide

This guide explains how to set up the Taruvi Python SDK repository and integrate it with the Taruvi platform.

## Repository Setup

### 1. Initialize Git Repository

```bash
cd /home/neha/Projects/Taruvi_new/taruvi-python-sdk
git init
git add .
git commit -m "Initial commit: Taruvi Python SDK v0.1.0"
```

### 2. Create GitHub Repository

1. Go to GitHub: https://github.com/new
2. Repository name: `taruvi-python-sdk`
3. Description: "Official Python SDK for Taruvi Cloud Platform"
4. Make it **Public** (or Private if preferred)
5. Do NOT initialize with README, .gitignore, or license (we already have these)

### 3. Push to GitHub

```bash
# Add remote
git remote add origin https://github.com/YOUR_USERNAME/taruvi-python-sdk.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Development Setup

### For SDK Development

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/taruvi-python-sdk.git
cd taruvi-python-sdk

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

## Platform Integration

### Option 1: Install from Local Path (Development)

In the Taruvi platform repository:

```bash
# Install SDK from local path
pip install -e /home/neha/Projects/Taruvi_new/taruvi-python-sdk
```

Add to `requirements.txt`:
```txt
# For development (local installation)
-e /home/neha/Projects/Taruvi_new/taruvi-python-sdk
```

### Option 2: Install from Git URL

Once pushed to GitHub, you can install directly:

```bash
# Install from GitHub
pip install git+https://github.com/YOUR_USERNAME/taruvi-python-sdk.git
```

Add to `requirements.txt`:
```txt
# Install from GitHub (main branch)
git+https://github.com/YOUR_USERNAME/taruvi-python-sdk.git@main

# Or specific version/tag
git+https://github.com/YOUR_USERNAME/taruvi-python-sdk.git@v0.1.0
```

### Option 3: Install from PyPI (Production)

After publishing to PyPI:

```bash
# Install from PyPI
pip install taruvi
```

Add to `requirements.txt`:
```txt
taruvi>=0.1.0
```

## Docker Setup

### Update Platform Dockerfile

In your Taruvi platform `Dockerfile`:

```dockerfile
# Option 1: Install from PyPI (when published)
RUN pip install taruvi>=0.1.0

# Option 2: Install from GitHub
RUN pip install git+https://github.com/YOUR_USERNAME/taruvi-python-sdk.git@main

# Option 3: Copy local SDK (for development)
COPY ../taruvi-python-sdk /tmp/taruvi-python-sdk
RUN pip install /tmp/taruvi-python-sdk && rm -rf /tmp/taruvi-python-sdk
```

### Update docker-compose.yml

For local development with editable install:

```yaml
services:
  web:
    volumes:
      # Mount SDK source for development
      - ../taruvi-python-sdk:/taruvi-python-sdk:ro
    environment:
      # SDK will be installed in editable mode
      - PYTHONPATH=/taruvi-python-sdk/src:$PYTHONPATH
```

## Publishing to PyPI

### 1. Configure PyPI Account

```bash
# Install twine
pip install twine

# Configure PyPI credentials
# Create ~/.pypirc:
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR-API-TOKEN

[testpypi]
username = __token__
password = pypi-YOUR-TESTPYPI-TOKEN
```

### 2. Build Package

```bash
# Install build tools
pip install build

# Build distribution
python -m build

# This creates:
# - dist/taruvi-0.1.0-py3-none-any.whl
# - dist/taruvi-0.1.0.tar.gz
```

### 3. Test on TestPyPI First

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ taruvi
```

### 4. Publish to PyPI

```bash
# Upload to PyPI
twine upload dist/*

# Now anyone can install:
pip install taruvi
```

## Version Management

### Updating Version

Edit `pyproject.toml`:

```toml
[project]
version = "0.2.0"  # Update version here
```

### Creating Releases

```bash
# Tag release
git tag -a v0.2.0 -m "Release version 0.2.0"
git push origin v0.2.0

# Build and publish
python -m build
twine upload dist/*
```

## CI/CD Setup

### GitHub Actions

The repository includes `.github/workflows/ci.yml` which:

- Runs tests on Python 3.10, 3.11, 3.12
- Checks code formatting (black)
- Runs linter (ruff)
- Type checks (mypy)
- Builds package
- Uploads coverage to Codecov

### Enable GitHub Actions

1. Go to repository settings
2. Enable GitHub Actions
3. Configure secrets if needed (PyPI tokens, etc.)

### Badge Setup

Add badges to README.md:

```markdown
[![CI](https://github.com/YOUR_USERNAME/taruvi-python-sdk/workflows/CI/badge.svg)](https://github.com/YOUR_USERNAME/taruvi-python-sdk/actions)
[![codecov](https://codecov.io/gh/YOUR_USERNAME/taruvi-python-sdk/branch/main/graph/badge.svg)](https://codecov.io/gh/YOUR_USERNAME/taruvi-python-sdk)
[![PyPI version](https://badge.fury.io/py/taruvi.svg)](https://badge.fury.io/py/taruvi)
[![Python Versions](https://img.shields.io/pypi/pyversions/taruvi.svg)](https://pypi.org/project/taruvi/)
```

## Testing Integration

### Test in Platform

1. **Install SDK in platform:**
   ```bash
   cd /home/neha/Projects/Taruvi_new/Taruvi
   pip install -e ../taruvi-python-sdk
   ```

2. **Verify installation:**
   ```python
   python manage.py shell
   >>> from taruvi import Client, SyncClient
   >>> print("SDK installed successfully!")
   ```

3. **Test with example function:**
   - Upload `example_sdk_function.py` to Taruvi
   - Execute via API
   - Verify SDK client is available

### Run SDK Tests

```bash
cd /home/neha/Projects/Taruvi_new/taruvi-python-sdk

# Run all tests
pytest

# Run with coverage
pytest --cov=taruvi --cov-report=html

# Open coverage report
open htmlcov/index.html
```

## Documentation

### Build Documentation (Optional)

If you want to add Sphinx documentation:

```bash
# Install Sphinx
pip install sphinx sphinx-rtd-theme

# Initialize docs
sphinx-quickstart docs

# Build docs
cd docs
make html
```

## Troubleshooting

### SDK Not Found in Functions

If functions can't import the SDK:

1. Verify SDK is installed in platform environment:
   ```bash
   pip list | grep taruvi
   ```

2. Check Docker container (if using Docker):
   ```bash
   docker exec taruvi_web pip list | grep taruvi
   ```

3. Verify import in Django shell:
   ```bash
   python manage.py shell
   >>> from taruvi import Client
   ```

### Import Errors

If you get import errors:

1. Check Python version (requires >=3.10)
2. Reinstall SDK: `pip install --force-reinstall -e path/to/sdk`
3. Clear Python cache: `find . -type d -name __pycache__ -exec rm -rf {} +`

## Repository Structure

```
taruvi-python-sdk/
├── .github/
│   └── workflows/
│       └── ci.yml              # CI/CD pipeline
├── src/
│   └── taruvi/                 # SDK source code
│       ├── __init__.py
│       ├── client.py
│       ├── sync_client.py
│       ├── config.py
│       ├── exceptions.py
│       ├── http_client.py
│       ├── runtime.py
│       └── modules/
│           ├── functions.py
│           ├── database.py
│           └── auth.py
├── tests/                      # Test files
├── .gitignore
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── pyproject.toml
└── SETUP_GUIDE.md             # This file
```

## Next Steps

1. ✅ Repository is set up
2. ⬜ Push to GitHub
3. ⬜ Set up CI/CD (GitHub Actions)
4. ⬜ Add tests
5. ⬜ Publish to PyPI (optional)
6. ⬜ Update platform to use SDK from new repository

## Support

- **Issues**: https://github.com/YOUR_USERNAME/taruvi-python-sdk/issues
- **Discussions**: https://github.com/YOUR_USERNAME/taruvi-python-sdk/discussions
- **Email**: support@taruvi.cloud
