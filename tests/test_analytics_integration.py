"""
Integration tests for Analytics API module.

IMPORTANT: These are REAL integration tests - NO MOCKS!
- Executes REAL analytics queries against backend
- Tests query execution with various parameters
- Verifies response structure and data

Setup:
    1. Ensure .env is configured with backend URL and credentials
    2. Backend must have analytics queries configured
    3. Run: RUN_INTEGRATION_TESTS=1 pytest tests/test_analytics_integration.py -v

Note:
    - Tests assume analytics queries exist in the backend
    - If queries don't exist, tests will skip gracefully
    - Common test queries: "test-query", "user-signups", "monthly-stats"
"""

import pytest


# ============================================================================
# Analytics Query Execution Tests - Async
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_execute_analytics_query_async(async_analytics_module):
    """
    Test executing an analytics query (async).

    Executes a real analytics query and verifies response structure.
    """
    try:
        # Execute analytics query
        result = await async_analytics_module.execute(
            "test-query",
            params={}
        )

        # Verify response structure
        assert result is not None
        assert isinstance(result, dict), "Response should be a dictionary"
        assert "data" in result, "Response should contain 'data' key"

    except Exception as e:
        error_msg = str(e).lower()
        if "not found" in error_msg or "does not exist" in error_msg:
            pytest.skip(f"Skipping: Analytics query 'test-query' not configured - {str(e)}")
        elif "permission" in error_msg or "not enabled" in error_msg:
            pytest.skip(f"Skipping: Analytics not accessible - {str(e)}")
        raise


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execute_with_params_async(async_analytics_module):
    """
    Test executing analytics query with parameters (async).

    Executes query with date range and filters.
    """
    try:
        # Execute query with parameters
        result = await async_analytics_module.execute(
            "test-query",
            params={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            }
        )

        # Verify response structure
        assert result is not None
        assert isinstance(result, dict)
        assert "data" in result

    except Exception as e:
        error_msg = str(e).lower()
        if "not found" in error_msg or "does not exist" in error_msg:
            pytest.skip(f"Skipping: Analytics query not configured - {str(e)}")
        elif "permission" in error_msg or "not enabled" in error_msg:
            pytest.skip(f"Skipping: Analytics not accessible - {str(e)}")
        raise


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execute_with_grouping_async(async_analytics_module):
    """
    Test executing analytics query with grouping (async).

    Executes query with group_by parameter.
    """
    try:
        # Execute query with grouping
        result = await async_analytics_module.execute(
            "test-query",
            params={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "group_by": "month"
            }
        )

        # Verify response structure
        assert result is not None
        assert isinstance(result, dict)
        assert "data" in result

    except Exception as e:
        error_msg = str(e).lower()
        if "not found" in error_msg or "does not exist" in error_msg:
            pytest.skip(f"Skipping: Analytics query not configured - {str(e)}")
        elif "permission" in error_msg or "not enabled" in error_msg:
            pytest.skip(f"Skipping: Analytics not accessible - {str(e)}")
        raise


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execute_with_filters_async(async_analytics_module):
    """
    Test executing analytics query with filters (async).

    Executes query with custom filter parameters.
    """
    try:
        # Execute query with filters
        result = await async_analytics_module.execute(
            "test-query",
            params={
                "status": "active",
                "category": "test"
            }
        )

        # Verify response structure
        assert result is not None
        assert isinstance(result, dict)
        assert "data" in result

    except Exception as e:
        error_msg = str(e).lower()
        if "not found" in error_msg or "does not exist" in error_msg:
            pytest.skip(f"Skipping: Analytics query not configured - {str(e)}")
        elif "permission" in error_msg or "not enabled" in error_msg:
            pytest.skip(f"Skipping: Analytics not accessible - {str(e)}")
        raise


# ============================================================================
# Analytics Query Execution Tests - Sync
# ============================================================================

@pytest.mark.integration
def test_execute_analytics_query_sync(sync_analytics_module):
    """
    Test executing an analytics query (sync).

    Executes a real analytics query and verifies response structure.
    """
    try:
        # Execute analytics query
        result = sync_analytics_module.execute(
            "test-query",
            params={}
        )

        # Verify response structure
        assert result is not None
        assert isinstance(result, dict), "Response should be a dictionary"
        assert "data" in result, "Response should contain 'data' key"

    except Exception as e:
        error_msg = str(e).lower()
        if "not found" in error_msg or "does not exist" in error_msg:
            pytest.skip(f"Skipping: Analytics query 'test-query' not configured - {str(e)}")
        elif "permission" in error_msg or "not enabled" in error_msg:
            pytest.skip(f"Skipping: Analytics not accessible - {str(e)}")
        raise


@pytest.mark.integration
def test_execute_with_params_sync(sync_analytics_module):
    """
    Test executing analytics query with parameters (sync).

    Executes query with date range and filters.
    """
    try:
        # Execute query with parameters
        result = sync_analytics_module.execute(
            "test-query",
            params={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            }
        )

        # Verify response structure
        assert result is not None
        assert isinstance(result, dict)
        assert "data" in result

    except Exception as e:
        error_msg = str(e).lower()
        if "not found" in error_msg or "does not exist" in error_msg:
            pytest.skip(f"Skipping: Analytics query not configured - {str(e)}")
        elif "permission" in error_msg or "not enabled" in error_msg:
            pytest.skip(f"Skipping: Analytics not accessible - {str(e)}")
        raise


@pytest.mark.integration
def test_execute_with_grouping_sync(sync_analytics_module):
    """
    Test executing analytics query with grouping (sync).

    Executes query with group_by parameter.
    """
    try:
        # Execute query with grouping
        result = sync_analytics_module.execute(
            "test-query",
            params={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "group_by": "month"
            }
        )

        # Verify response structure
        assert result is not None
        assert isinstance(result, dict)
        assert "data" in result

    except Exception as e:
        error_msg = str(e).lower()
        if "not found" in error_msg or "does not exist" in error_msg:
            pytest.skip(f"Skipping: Analytics query not configured - {str(e)}")
        elif "permission" in error_msg or "not enabled" in error_msg:
            pytest.skip(f"Skipping: Analytics not accessible - {str(e)}")
        raise


@pytest.mark.integration
def test_execute_with_filters_sync(sync_analytics_module):
    """
    Test executing analytics query with filters (sync).

    Executes query with custom filter parameters.
    """
    try:
        # Execute query with filters
        result = sync_analytics_module.execute(
            "test-query",
            params={
                "status": "active",
                "category": "test"
            }
        )

        # Verify response structure
        assert result is not None
        assert isinstance(result, dict)
        assert "data" in result

    except Exception as e:
        error_msg = str(e).lower()
        if "not found" in error_msg or "does not exist" in error_msg:
            pytest.skip(f"Skipping: Analytics query not configured - {str(e)}")
        elif "permission" in error_msg or "not enabled" in error_msg:
            pytest.skip(f"Skipping: Analytics not accessible - {str(e)}")
        raise


# ============================================================================
# Error Handling Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_execute_nonexistent_query_async(async_analytics_module):
    """
    Test executing a non-existent analytics query (async).

    Should raise appropriate error when query doesn't exist.
    """
    from taruvi.exceptions import NotFoundError, APIError

    try:
        await async_analytics_module.execute(
            "nonexistent-query-12345",
            params={}
        )
        # If no error, the query somehow exists - skip test
        pytest.skip("Query unexpectedly exists")

    except (NotFoundError, APIError) as e:
        # Expected behavior - query not found
        assert "not found" in str(e).lower() or "does not exist" in str(e).lower()

    except Exception as e:
        # Other errors might indicate permission issues
        error_msg = str(e).lower()
        if "permission" in error_msg or "not enabled" in error_msg:
            pytest.skip(f"Skipping: Analytics not accessible - {str(e)}")
        raise


@pytest.mark.integration
def test_execute_nonexistent_query_sync(sync_analytics_module):
    """
    Test executing a non-existent analytics query (sync).

    Should raise appropriate error when query doesn't exist.
    """
    from taruvi.exceptions import NotFoundError, APIError

    try:
        sync_analytics_module.execute(
            "nonexistent-query-12345",
            params={}
        )
        # If no error, the query somehow exists - skip test
        pytest.skip("Query unexpectedly exists")

    except (NotFoundError, APIError) as e:
        # Expected behavior - query not found
        assert "not found" in str(e).lower() or "does not exist" in str(e).lower()

    except Exception as e:
        # Other errors might indicate permission issues
        error_msg = str(e).lower()
        if "permission" in error_msg or "not enabled" in error_msg:
            pytest.skip(f"Skipping: Analytics not accessible - {str(e)}")
        raise
