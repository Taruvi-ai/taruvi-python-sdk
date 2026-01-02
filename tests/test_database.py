"""Test database module - query builders and CRUD operations."""

import pytest
from unittest.mock import AsyncMock

from taruvi.modules.database import (
    DatabaseModule,
    SyncDatabaseModule,
    QueryBuilder,
    SyncQueryBuilder,
    _BaseQueryBuilder
)


# ============================================================================
# Test Base Query Builder (Shared Logic)
# ============================================================================

def test_base_query_builder_filters():
    """Test base query builder filter logic."""
    builder = _BaseQueryBuilder("users", "test-app")

    # Test eq filter
    builder._add_filter("status", "eq", "active")
    assert builder._filters["status"] == "active"

    # Test other operators
    builder._add_filter("age", "gte", 18)
    assert builder._filters["age__gte"] == 18

    builder._add_filter("name", "contains", "john")
    assert builder._filters["name__contains"] == "john"


def test_base_query_builder_sort():
    """Test base query builder sort logic."""
    builder = _BaseQueryBuilder("users", "test-app")

    builder._set_sort("created_at", "desc")
    assert builder._sort_field == "created_at"
    assert builder._sort_order == "desc"


def test_base_query_builder_pagination():
    """Test base query builder pagination logic."""
    builder = _BaseQueryBuilder("users", "test-app")

    builder._set_limit(10)
    builder._set_offset(20)

    assert builder._limit_value == 10
    assert builder._offset_value == 20


def test_base_query_builder_populate():
    """Test base query builder populate logic."""
    builder = _BaseQueryBuilder("posts", "test-app")

    builder._add_populate("author", "comments")
    assert "author" in builder._populate_fields
    assert "comments" in builder._populate_fields


def test_base_query_builder_build_params():
    """Test building query parameters."""
    builder = _BaseQueryBuilder("users", "test-app")

    builder._add_filter("status", "eq", "active")
    builder._add_filter("age", "gte", 18)
    builder._set_sort("created_at", "desc")
    builder._set_limit(10)
    builder._set_offset(20)
    builder._add_populate("profile")

    params = builder.build_params()

    assert params["status"] == "active"
    assert params["age__gte"] == 18
    assert params["_sort"] == "created_at"
    assert params["_order"] == "desc"
    assert params["limit"] == 10
    assert params["offset"] == 20
    assert params["populate"] == "profile"


# ============================================================================
# Test Async QueryBuilder
# ============================================================================

@pytest.mark.asyncio
async def test_async_query_builder_chaining(mock_async_client):
    """Test async query builder method chaining."""
    db = DatabaseModule(mock_async_client)
    query = db.query("users")

    # Chain methods
    result_query = (query
                    .filter("status", "eq", "active")
                    .filter("age", "gte", 18)
                    .sort("created_at", "desc")
                    .limit(10)
                    .offset(20))

    # Should return same instance for chaining
    assert isinstance(result_query, QueryBuilder)

    # Check internal state
    assert result_query._filters["status"] == "active"
    assert result_query._filters["age__gte"] == 18
    assert result_query._sort_field == "created_at"
    assert result_query._limit_value == 10


@pytest.mark.asyncio
async def test_async_query_builder_get(mock_async_client):
    """Test async query builder get method."""
    db = DatabaseModule(mock_async_client)

    # Mock response
    mock_async_client._http_client.get.return_value = {
        "data": [
            {"id": 1, "name": "Alice", "status": "active"},
            {"id": 2, "name": "Bob", "status": "active"}
        ]
    }

    results = await db.query("users").filter("status", "eq", "active").get()

    # Verify HTTP call
    mock_async_client._http_client.get.assert_called_once()
    call_args = mock_async_client._http_client.get.call_args

    # Check path
    path = call_args[0][0]
    assert "/datatables/users/data/" in path

    # Check params
    params = call_args[1]["params"]
    assert params["status"] == "active"

    # Verify results
    assert len(results) == 2
    assert results[0].name == "Alice"
    assert results[1].name == "Bob"


@pytest.mark.asyncio
async def test_async_query_builder_first(mock_async_client):
    """Test async query builder first method."""
    db = DatabaseModule(mock_async_client)

    # Mock response
    mock_async_client._http_client.get.return_value = {
        "data": [{"id": 1, "name": "Alice"}]
    }

    result = await db.query("users").filter("id", "eq", 1).first()

    # Should auto-limit to 1
    call_args = mock_async_client._http_client.get.call_args
    params = call_args[1]["params"]
    assert params["limit"] == 1

    # Verify result
    assert result is not None
    assert result.name == "Alice"


@pytest.mark.asyncio
async def test_async_query_builder_count(mock_async_client):
    """Test async query builder count method."""
    db = DatabaseModule(mock_async_client)

    # Mock response
    mock_async_client._http_client.get.return_value = {
        "total": 42
    }

    count = await db.query("users").filter("status", "eq", "active").count()

    # Verify count param added
    call_args = mock_async_client._http_client.get.call_args
    params = call_args[1]["params"]
    assert params["_count"] == "true"

    # Verify count
    assert count == 42


# ============================================================================
# Test Async DatabaseModule CRUD
# ============================================================================

@pytest.mark.asyncio
async def test_async_database_create(mock_async_client):
    """Test async database create method."""
    db = DatabaseModule(mock_async_client)

    # Mock response
    mock_async_client._http_client.post.return_value = {
        "data": {"id": 1, "name": "Alice", "email": "alice@example.com"}
    }

    result = await db.create("users", {"name": "Alice", "email": "alice@example.com"})

    # Verify HTTP call
    mock_async_client._http_client.post.assert_called_once()
    call_args = mock_async_client._http_client.post.call_args

    assert "/datatables/users/data/" in call_args[0][0]
    assert call_args[1]["json"]["name"] == "Alice"

    # Verify result
    assert result.id == 1
    assert result.name == "Alice"


@pytest.mark.asyncio
async def test_async_database_update(mock_async_client):
    """Test async database update method."""
    db = DatabaseModule(mock_async_client)

    # Mock response
    mock_async_client._http_client.put.return_value = {
        "data": {"id": 1, "name": "Alice Updated"}
    }

    result = await db.update("users", 1, {"name": "Alice Updated"})

    # Verify HTTP call
    mock_async_client._http_client.put.assert_called_once()
    call_args = mock_async_client._http_client.put.call_args

    assert "/datatables/users/data/1/" in call_args[0][0]
    assert call_args[1]["json"]["name"] == "Alice Updated"


@pytest.mark.asyncio
async def test_async_database_delete(mock_async_client):
    """Test async database delete method."""
    db = DatabaseModule(mock_async_client)

    await db.delete("users", 1)

    # Verify HTTP call
    mock_async_client._http_client.delete.assert_called_once()
    call_args = mock_async_client._http_client.delete.call_args

    assert "/datatables/users/data/1/" in call_args[0][0]


# ============================================================================
# Test Sync QueryBuilder
# ============================================================================

def test_sync_query_builder_chaining(mock_sync_client):
    """Test sync query builder method chaining."""
    db = SyncDatabaseModule(mock_sync_client)
    query = db.query("users")

    # Chain methods
    result_query = (query
                    .filter("status", "eq", "active")
                    .sort("created_at", "desc")
                    .limit(10))

    # Should return same instance for chaining
    assert isinstance(result_query, SyncQueryBuilder)

    # Check internal state
    assert result_query._filters["status"] == "active"
    assert result_query._sort_field == "created_at"


def test_sync_query_builder_get(mock_sync_client):
    """Test sync query builder get method."""
    db = SyncDatabaseModule(mock_sync_client)

    # Mock response
    mock_sync_client._http.get.return_value = {
        "data": [
            {"id": 1, "name": "Alice"}
        ]
    }

    results = db.query("users").filter("status", "eq", "active").get()

    # Verify HTTP call
    mock_sync_client._http.get.assert_called_once()

    # Verify results
    assert len(results) == 1
    assert results[0].name == "Alice"


# ============================================================================
# Test Sync/Async Equivalence
# ============================================================================

def test_database_sync_async_equivalence(mock_async_client, mock_sync_client):
    """Test that async and sync database modules have same API."""
    async_db = DatabaseModule(mock_async_client)
    sync_db = SyncDatabaseModule(mock_sync_client)

    # Get public methods
    async_methods = {m for m in dir(async_db) if not m.startswith('_')}
    sync_methods = {m for m in dir(sync_db) if not m.startswith('_')}

    # Should have the same public API
    assert async_methods == sync_methods


def test_query_builder_sync_async_equivalence(mock_async_client, mock_sync_client):
    """Test that async and sync query builders have same API."""
    async_query = QueryBuilder(mock_async_client, "users")
    sync_query = SyncQueryBuilder(mock_sync_client, "users")

    # Get public methods (excluding inherited object methods)
    async_methods = {m for m in dir(async_query) if not m.startswith('_')}
    sync_methods = {m for m in dir(sync_query) if not m.startswith('_')}

    # Should have the same public API
    assert async_methods == sync_methods
