"""
Integration tests for Database search() method.

IMPORTANT: These are REAL integration tests - NO MOCKS!
- Makes actual HTTP requests to Taruvi backend
- Tests full-text search via ?search= query parameter
- Requires a table with search_vector field configured

Setup:
    1. Ensure .env is configured with backend URL and credentials
    2. Backend must have a table with search_vector field (x-search-fields in schema)
    3. Run: RUN_INTEGRATION_TESTS=1 pytest tests/test_database_search.py -v

Note:
    - Tests use "test_table" by default (override via TARUVI_TEST_SEARCH_TABLE env var)
    - If table has no search_vector field, search param is silently ignored by backend
"""

import os
import pytest


SEARCH_TABLE = os.getenv("TARUVI_TEST_SEARCH_TABLE", "test_table")


# ============================================================================
# Search Tests - Async
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_basic_async(async_database_module):
    """Test basic full-text search (async)."""
    try:
        result = await (
            async_database_module.from_(SEARCH_TABLE)
            .search("test")
            .execute()
        )

        assert result is not None
        assert isinstance(result, dict)

    except Exception as e:
        error_msg = str(e).lower()
        if "not found" in error_msg or "does not exist" in error_msg:
            pytest.skip(f"Skipping: Table '{SEARCH_TABLE}' not accessible - {e}")
        raise


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_with_filters_async(async_database_module):
    """Test search combined with filters (async)."""
    try:
        result = await (
            async_database_module.from_(SEARCH_TABLE)
            .search("test")
            .filter("id", "gt", 0)
            .page_size(5)
            .execute()
        )

        assert result is not None
        assert isinstance(result, dict)

    except Exception as e:
        error_msg = str(e).lower()
        if "not found" in error_msg or "does not exist" in error_msg:
            pytest.skip(f"Skipping: Table '{SEARCH_TABLE}' not accessible - {e}")
        raise


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_with_sort_and_pagination_async(async_database_module):
    """Test search combined with sorting and pagination (async)."""
    try:
        result = await (
            async_database_module.from_(SEARCH_TABLE)
            .search("test")
            .sort("created_at", "desc")
            .page_size(10)
            .page(1)
            .execute()
        )

        assert result is not None
        assert isinstance(result, dict)

    except Exception as e:
        error_msg = str(e).lower()
        if "not found" in error_msg or "does not exist" in error_msg:
            pytest.skip(f"Skipping: Table '{SEARCH_TABLE}' not accessible - {e}")
        raise


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_no_results_async(async_database_module):
    """Test search with query that returns no results (async)."""
    try:
        result = await (
            async_database_module.from_(SEARCH_TABLE)
            .search("zzzznonexistentterm99999")
            .execute()
        )

        assert result is not None
        assert isinstance(result, dict)
        # Should return empty results, not error
        results_data = result.get("results", result.get("data", []))
        if isinstance(results_data, list):
            assert len(results_data) == 0

    except Exception as e:
        error_msg = str(e).lower()
        if "not found" in error_msg or "does not exist" in error_msg:
            pytest.skip(f"Skipping: Table '{SEARCH_TABLE}' not accessible - {e}")
        raise


# ============================================================================
# Search Tests - Sync
# ============================================================================

@pytest.mark.integration
def test_search_basic_sync(sync_database_module):
    """Test basic full-text search (sync)."""
    try:
        result = (
            sync_database_module.from_(SEARCH_TABLE)
            .search("test")
            .execute()
        )

        assert result is not None
        assert isinstance(result, dict)

    except Exception as e:
        error_msg = str(e).lower()
        if "not found" in error_msg or "does not exist" in error_msg:
            pytest.skip(f"Skipping: Table '{SEARCH_TABLE}' not accessible - {e}")
        raise


@pytest.mark.integration
def test_search_with_filters_sync(sync_database_module):
    """Test search combined with filters (sync)."""
    try:
        result = (
            sync_database_module.from_(SEARCH_TABLE)
            .search("test")
            .filter("id", "gt", 0)
            .page_size(5)
            .execute()
        )

        assert result is not None
        assert isinstance(result, dict)

    except Exception as e:
        error_msg = str(e).lower()
        if "not found" in error_msg or "does not exist" in error_msg:
            pytest.skip(f"Skipping: Table '{SEARCH_TABLE}' not accessible - {e}")
        raise


@pytest.mark.integration
def test_search_with_sort_and_pagination_sync(sync_database_module):
    """Test search combined with sorting and pagination (sync)."""
    try:
        result = (
            sync_database_module.from_(SEARCH_TABLE)
            .search("test")
            .sort("created_at", "desc")
            .page_size(10)
            .page(1)
            .execute()
        )

        assert result is not None
        assert isinstance(result, dict)

    except Exception as e:
        error_msg = str(e).lower()
        if "not found" in error_msg or "does not exist" in error_msg:
            pytest.skip(f"Skipping: Table '{SEARCH_TABLE}' not accessible - {e}")
        raise


@pytest.mark.integration
def test_search_no_results_sync(sync_database_module):
    """Test search with query that returns no results (sync)."""
    try:
        result = (
            sync_database_module.from_(SEARCH_TABLE)
            .search("zzzznonexistentterm99999")
            .execute()
        )

        assert result is not None
        assert isinstance(result, dict)
        results_data = result.get("results", result.get("data", []))
        if isinstance(results_data, list):
            assert len(results_data) == 0

    except Exception as e:
        error_msg = str(e).lower()
        if "not found" in error_msg or "does not exist" in error_msg:
            pytest.skip(f"Skipping: Table '{SEARCH_TABLE}' not accessible - {e}")
        raise


# ============================================================================
# QueryBuilder search() Unit Tests (no backend needed)
# ============================================================================

def test_search_sets_param():
    """Test that search() adds 'search' to built query params."""
    from taruvi._sync.modules.database import _BaseQueryBuilder

    class FakeConfig:
        app_slug = "test"

    qb = _BaseQueryBuilder(http_client=None, config=FakeConfig(), table_name="t")
    qb._set_search("hello world")
    params = qb.build_params()
    assert params.get("search") == "hello world"


def test_search_not_set_by_default():
    """Test that search param is absent when search() is not called."""
    from taruvi._sync.modules.database import _BaseQueryBuilder

    class FakeConfig:
        app_slug = "test"

    qb = _BaseQueryBuilder(http_client=None, config=FakeConfig(), table_name="t")
    params = qb.build_params()
    assert "search" not in params
