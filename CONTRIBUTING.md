# Contributing to Taruvi Python SDK

Thank you for your interest in contributing to the Taruvi Python SDK! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git
- pip

### Setup Development Environment

1. **Clone the repository**

```bash
git clone https://github.com/taruvi-ai/taruvi-python-sdk.git
cd taruvi-python-sdk
```

2. **Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install in development mode**

```bash
pip install -e ".[dev]"
```

This installs the SDK in editable mode along with development dependencies (pytest, black, ruff, mypy).

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=taruvi --cov-report=html

# Run specific test file
pytest tests/test_client.py -v
```

### Code Formatting

We use `black` for code formatting:

```bash
# Format all code
black src/

# Check formatting without changes
black --check src/
```

### Linting

We use `ruff` for linting:

```bash
# Lint code
ruff check src/

# Auto-fix issues
ruff check --fix src/
```

### Type Checking

We use `mypy` for type checking:

```bash
# Type check
mypy src/
```

### Before Committing

Run all checks:

```bash
# Format code
black src/ tests/

# Lint
ruff check --fix src/ tests/

# Type check
mypy src/

# Run tests
pytest
```

## Pull Request Process

1. **Fork the repository** and create your branch from `main`

```bash
git checkout -b feature/my-feature
```

2. **Make your changes** following our coding standards

3. **Add tests** for any new functionality

4. **Update documentation** if needed (README.md, docstrings)

5. **Ensure all tests pass** and code is formatted

6. **Commit your changes** with clear commit messages

```bash
git commit -m "Add: new feature description"
```

We use conventional commit messages:
- `Add:` for new features
- `Fix:` for bug fixes
- `Update:` for enhancements to existing features
- `Refactor:` for code restructuring
- `Docs:` for documentation changes
- `Test:` for test additions/updates

7. **Push to your fork**

```bash
git push origin feature/my-feature
```

8. **Open a Pull Request** against the `main` branch

## Coding Standards

### Python Style

- Follow PEP 8
- Use type hints for all function parameters and returns
- Maximum line length: 100 characters
- Use descriptive variable names

### Documentation

- Add docstrings to all public functions, classes, and modules
- Use Google or NumPy docstring format
- Include examples in docstrings where appropriate

Example:

```python
def execute_function(
    function_slug: str,
    params: dict[str, Any],
    timeout: int = 30
) -> dict[str, Any]:
    """
    Execute a Taruvi function.

    Args:
        function_slug: Slug of the function to execute
        params: Parameters to pass to the function
        timeout: Request timeout in seconds

    Returns:
        dict: Function execution result

    Raises:
        NotFoundError: If function not found
        TimeoutError: If request times out

    Example:
        ```python
        result = await client.functions.execute(
            "process-order",
            params={"order_id": 123}
        )
        ```
    """
    # Implementation
```

### Testing

- Write tests for all new functionality
- Aim for >80% code coverage
- Use descriptive test names: `test_should_return_error_when_function_not_found`
- Use pytest fixtures for common setup

## Reporting Bugs

When reporting bugs, please include:

1. **Description**: Clear description of the bug
2. **Steps to reproduce**: Minimal code example
3. **Expected behavior**: What should happen
4. **Actual behavior**: What actually happens
5. **Environment**: Python version, SDK version, OS
6. **Logs**: Any relevant error messages or logs

## Feature Requests

When requesting features, please include:

1. **Use case**: Why is this feature needed?
2. **Proposed solution**: How should it work?
3. **Alternatives**: Any alternative solutions considered?

## Questions?

If you have questions:

- Check the [documentation](https://docs.taruvi.cloud)
- Open a [GitHub Discussion](https://github.com/taruvi-ai/taruvi-python-sdk/discussions)
- Contact us at support@taruvi.cloud

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
