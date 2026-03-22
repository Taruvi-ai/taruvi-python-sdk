"""
Integration tests for Functions API module.

IMPORTANT: These are REAL integration tests - NO MOCKS!
- Makes actual HTTP requests to Taruvi backend
- Requires running backend (local/dev/staging)
- Requires test function to exist in backend
- Tests will fail if API contract changes (this is GOOD!)

Setup:
    1. Copy .env.example to .env
    2. Fill in TARUVI_API_URL and credentials
    3. Ensure test backend has a function named "process-order" or update test_function_name
    4. Run: RUN_INTEGRATION_TESTS=1 pytest tests/test_functions_integration.py -v
"""

import pytest


# ============================================================================
# Execute Tests - Async (Real API Calls)
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_execute_async_sync_mode_real_api(async_functions_module, test_function_name):
    """
    Test execute in sync mode with REAL backend.

    This test makes an actual API call to execute a function.
    If the response structure changes, this test will catch it!
    """
    # Execute function synchronously on real backend
    result = await async_functions_module.execute(
        test_function_name,
        params={"order_id": 123},
        is_async=False
    )

    # Verify actual response structure from backend
    # SDK now returns extracted data directly (not wrapped in {"data": ...})
    assert result is not None
    assert "data" in result, "Response missing 'data' field - API contract changed!"
    assert "invocation" in result, "Response missing 'invocation' field - API contract changed!"

    # Verify invocation metadata
    invocation = result["invocation"]
    assert "id" in invocation
    assert "celery_task_id" in invocation
    assert "status" in invocation

    # In sync mode, status should be "completed"
    # (If this fails, backend behavior changed!)
    assert invocation["status"] in ["completed", "SUCCESS"], \
        f"Unexpected status: {invocation['status']}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execute_async_async_mode_real_api(async_functions_module, test_function_name):
    """
    Test execute in async mode with REAL backend.

    Creates a real background task and verifies it's pending.
    """
    # Execute function asynchronously on real backend
    result = await async_functions_module.execute(
        test_function_name,
        params={"order_id": 456},
        is_async=True
    )

    # Verify response structure (SDK returns extracted data)
    assert result is not None
    assert "invocation" in result

    invocation = result["invocation"]
    assert "celery_task_id" in invocation
    assert invocation["celery_task_id"] is not None

    # In async mode, task should be pending/running
    assert invocation["status"] in ["pending", "PENDING", "running", "STARTED"], \
        f"Unexpected async task status: {invocation['status']}"


# ============================================================================
# Get Result Tests - Async (Real API Calls)
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_result_async_real_api(async_functions_module, test_function_name):
    """
    Test complete workflow: execute async, then get result.

    This tests the REAL async execution flow end-to-end.
    """
    # Step 1: Execute function asynchronously
    execute_result = await async_functions_module.execute(
        test_function_name,
        params={"order_id": 789},
        is_async=True
    )

    task_id = execute_result["invocation"]["celery_task_id"]
    assert task_id is not None

    # Step 2: Get result using task_id
    # Note: This might be PENDING if function is still running
    result = await async_functions_module.get_result(task_id)

    # Verify actual result structure from backend (SDK returns extracted data)
    assert result is not None
    assert "task_id" in result
    assert result["task_id"] == task_id
    assert "status" in result

    # Status could be PENDING, SUCCESS, or FAILURE depending on timing
    assert result["status"] in ["PENDING", "SUCCESS", "FAILURE", "STARTED", "RETRY"]


# ============================================================================
# List Functions Tests - Async (Real API Calls)
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_async_real_api(async_functions_module):
    """
    Test listing functions from real backend.

    Verifies that list endpoint returns actual functions.
    """
    result = await async_functions_module.list(limit=10, offset=0)

    # Verify response structure (SDK returns extracted data)
    assert result is not None

    # Handle both response formats:
    # Format 1: {"count": X, "results": [...]}
    # Format 2: [...] (direct list)
    if isinstance(result, list):
        # Direct list format
        functions_list = result
    elif "results" in result:
        # Paginated format
        functions_list = result["results"]
    else:
        # Unknown format
        assert False, f"Unexpected response structure: {result}"

    # If there are functions, verify their structure
    if len(functions_list) > 0:
        function = functions_list[0]
        assert "id" in function or "slug" in function, \
            "Function object structure changed!"


# ============================================================================
# Get Function Details Tests - Async (Real API Calls)
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_async_real_api(async_functions_module, test_function_name):
    """
    Test getting function details from real backend.

    Verifies function metadata structure.
    """
    result = await async_functions_module.get(test_function_name)

    # Verify response structure (SDK returns extracted data directly)
    assert result is not None
    assert "id" in result or "slug" in result

    # Verify function name matches
    if "slug" in result:
        assert result["slug"] == test_function_name


# ============================================================================
# Sync Client Tests - Real API Calls
# ============================================================================

@pytest.mark.integration
def test_execute_sync_sync_mode_real_api(sync_functions_module, test_function_name):
    """
    Test sync client execute with REAL backend.

    Uses blocking sync client (no async/await).
    """
    # Execute function synchronously using sync client
    result = sync_functions_module.execute(
        test_function_name,
        params={"order_id": 321},
        is_async=False
    )

    # Verify actual response structure (SDK returns extracted data)
    assert result is not None
    assert "data" in result
    assert "invocation" in result

    invocation = result["invocation"]
    assert invocation["status"] in ["completed", "SUCCESS"]


@pytest.mark.integration
def test_get_result_sync_real_api(sync_functions_module, test_function_name):
    """
    Test sync client get_result with REAL backend.

    Complete workflow with sync client.
    """
    # Step 1: Execute async
    execute_result = sync_functions_module.execute(
        test_function_name,
        params={"order_id": 999},
        is_async=True
    )

    task_id = execute_result["invocation"]["celery_task_id"]

    # Step 2: Get result
    result = sync_functions_module.get_result(task_id)

    # Verify structure (SDK returns extracted data)
    assert result is not None
    assert result["task_id"] == task_id


# ============================================================================
# Error Handling Tests - Real API Errors
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_execute_nonexistent_function_real_api(async_functions_module):
    """
    Test executing non-existent function returns real 404 error.

    This verifies error handling with actual backend errors.
    """
    with pytest.raises(Exception) as exc_info:
        await async_functions_module.execute(
            "nonexistent-function-xyz-123",
            params={},
            is_async=False
        )

    # Verify we got a real error from backend
    # (Exact exception type depends on your SDK's error handling)
    assert exc_info.value is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_result_invalid_task_id_real_api(async_functions_module):
    """
    Test getting result for invalid task ID returns real error.
    """
    with pytest.raises(Exception) as exc_info:
        await async_functions_module.get_result("invalid-task-id-xyz")

    # Verify we got a real error from backend
    assert exc_info.value is not None


# ============================================================================
# Notes on Converting Your Other Tests
# ============================================================================

"""
To convert your other mocked tests to integration tests:

1. Remove all mock_async_http and mock_sync_http fixtures
2. Remove all mock_response definitions
3. Remove all mock assertions (assert_called_once, etc.)
4. Add @pytest.mark.integration decorator
5. Verify actual response structure instead of exact values
6. Test behavior, not implementation details

Example conversion:

BEFORE (mocked):
    mock_response = {"data": {"result": "success"}}
    mock_async_http.post.return_value = mock_response
    result = await module.execute("func")
    assert result == mock_response  # Exact match
    mock_async_http.post.assert_called_once()

AFTER (integration):
    result = await module.execute("func")  # Real API call
    assert "invocation" in result  # Structure check
    assert result is not None  # Behavior check

Benefits:
- No mock maintenance when API changes
- Tests break immediately when contract changes (good!)
- Tests real behavior, not assumptions
- Simpler test code
"""
