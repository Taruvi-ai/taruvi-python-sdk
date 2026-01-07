# Integration Tests Setup

## Quick Start

### 1. Install Dependencies
```bash
pip install pytest pytest-asyncio python-dotenv
```

### 2. Configure Environment
```bash
# Copy example env file
cp .env.example .env

# Edit .env and fill in your values
nano .env  # or use your favorite editor
```

Example `.env`:
```bash
TARUVI_API_URL=http://localhost:8000
TARUVI_API_KEY=your_api_key_here
TARUVI_TEST_APP_SLUG=test-app
RUN_INTEGRATION_TESTS=1
```

### 3. Run Integration Tests
```bash
# Run all integration tests
RUN_INTEGRATION_TESTS=1 pytest tests/test_functions_integration.py -v

# Or if you set RUN_INTEGRATION_TESTS=1 in .env:
pytest tests/test_functions_integration.py -v

# Run specific test
pytest tests/test_functions_integration.py::test_execute_async_sync_mode_real_api -v
```

## What Changed?

### Before (Mocked Tests)
```python
# Mocked response
mock_response = {"data": {...}, "invocation": {...}}
mock_async_http.post.return_value = mock_response

result = await module.execute("func")
assert result == mock_response  # Exact match
mock_async_http.post.assert_called_once()
```

**Problem:** If API changes, tests still pass but SDK breaks in production!

### After (Integration Tests)
```python
# Real API call - no mocks!
result = await module.execute("func")

# Verify structure, not exact values
assert "data" in result
assert "invocation" in result
```

**Benefit:** Tests break immediately when API contract changes!

## Test Requirements

Your test backend must have:
- A test function (default: "process-order")
- Accessible at TARUVI_API_URL
- Valid authentication configured

Update `test_function_name` in conftest.py if using different function.

## Common Issues

### Tests Skip Automatically
**Cause:** `RUN_INTEGRATION_TESTS` not set
**Fix:** `export RUN_INTEGRATION_TESTS=1` or add to `.env`

### Authentication Errors
**Cause:** Invalid API key or credentials
**Fix:** Check your `.env` file has correct `TARUVI_API_KEY`

### Function Not Found
**Cause:** Test function doesn't exist in backend
**Fix:** Create "process-order" function or update `test_function_name` in conftest.py

### Connection Refused
**Cause:** Backend not running
**Fix:** Start your Taruvi backend at `TARUVI_API_URL`

## Next Steps

Convert your other test files:
- `test_database.py` → `test_database_integration.py`
- `test_storage.py` → `test_storage_integration.py`
- `test_secrets.py` → `test_secrets_integration.py`

Follow the same pattern:
1. Remove mock fixtures
2. Use real client from conftest.py
3. Add `@pytest.mark.integration`
4. Verify structure, not exact values
