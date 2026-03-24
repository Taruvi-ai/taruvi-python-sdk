"""Unit tests for database edge CRUD and graph query builder methods."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from taruvi.config import TaruviConfig
from taruvi._async.modules.database import AsyncDatabaseModule, AsyncQueryBuilder
from taruvi._sync.modules.database import DatabaseModule, QueryBuilder


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_config():
    config = MagicMock(spec=TaruviConfig)
    config.app_slug = "test-app"
    config.api_url = "https://api.test.com"
    return config


@pytest.fixture
def mock_async_client(mock_config):
    client = MagicMock()
    client._config = mock_config
    client._http_client = AsyncMock()
    return client


@pytest.fixture
def mock_sync_client(mock_config):
    client = MagicMock()
    client._config = mock_config
    client._http_client = MagicMock()
    return client


@pytest.fixture
def async_db(mock_async_client):
    return AsyncDatabaseModule(mock_async_client)


@pytest.fixture
def sync_db(mock_sync_client):
    return DatabaseModule(mock_sync_client)


# ============================================================================
# Edge URL Tests — must match JS SDK: {table}_edges/data/
# ============================================================================

class TestEdgeURLs:
    """Verify edge endpoints use {table}_edges/data/ pattern (matching JS SDK)."""

    @pytest.mark.asyncio
    async def test_list_edges_url(self, async_db, mock_async_client):
        mock_async_client._http_client.get = AsyncMock(return_value={"data": [], "total": 0})
        await async_db.list_edges("employees")
        mock_async_client._http_client.get.assert_called_once()
        url = mock_async_client._http_client.get.call_args[0][0]
        assert url == "/api/apps/test-app/datatables/employees_edges/data/"

    @pytest.mark.asyncio
    async def test_create_edges_url(self, async_db, mock_async_client):
        mock_async_client._http_client.post = AsyncMock(return_value={"data": [], "total": 0})
        await async_db.create_edges("employees", [{"from": 1, "to": 2, "type": "manager"}])
        url = mock_async_client._http_client.post.call_args[0][0]
        assert url == "/api/apps/test-app/datatables/employees_edges/data/"

    @pytest.mark.asyncio
    async def test_update_edge_url(self, async_db, mock_async_client):
        mock_async_client._http_client.patch = AsyncMock(return_value={"data": {}})
        await async_db.update_edge("employees", 9, {"type": "dotted_line"})
        url = mock_async_client._http_client.patch.call_args[0][0]
        assert url == "/api/apps/test-app/datatables/employees_edges/data/9/"

    @pytest.mark.asyncio
    async def test_update_edge_string_id_url(self, async_db, mock_async_client):
        mock_async_client._http_client.patch = AsyncMock(return_value={"data": {}})
        await async_db.update_edge("employees", "abc-123", {"type": "manager"})
        url = mock_async_client._http_client.patch.call_args[0][0]
        assert url == "/api/apps/test-app/datatables/employees_edges/data/abc-123/"

    @pytest.mark.asyncio
    async def test_delete_edges_url(self, async_db, mock_async_client):
        mock_async_client._http_client.delete = AsyncMock(return_value={"deleted": 2})
        await async_db.delete_edges("employees", [9, 10])
        url = mock_async_client._http_client.delete.call_args[0][0]
        assert url == "/api/apps/test-app/datatables/employees_edges/data/"

    def test_sync_list_edges_url(self, sync_db, mock_sync_client):
        mock_sync_client._http_client.get = MagicMock(return_value={"data": [], "total": 0})
        sync_db.list_edges("employees")
        url = mock_sync_client._http_client.get.call_args[0][0]
        assert url == "/api/apps/test-app/datatables/employees_edges/data/"

    def test_sync_create_edges_url(self, sync_db, mock_sync_client):
        mock_sync_client._http_client.post = MagicMock(return_value={"data": [], "total": 0})
        sync_db.create_edges("employees", [{"from": 1, "to": 2, "type": "manager"}])
        url = mock_sync_client._http_client.post.call_args[0][0]
        assert url == "/api/apps/test-app/datatables/employees_edges/data/"


# ============================================================================
# Edge Request Body Tests
# ============================================================================

class TestEdgeRequestBody:
    """Verify edge request bodies match JS SDK behavior."""

    @pytest.mark.asyncio
    async def test_create_edges_passes_body_as_array(self, async_db, mock_async_client):
        """JS SDK sends array of edge objects directly."""
        mock_async_client._http_client.post = AsyncMock(return_value={"data": [], "total": 0})
        edges = [
            {"from": 5, "to": 2, "type": "manager"},
            {"from": 5, "to": 3, "type": "dotted_line", "metadata": {"project": "AI"}},
        ]
        await async_db.create_edges("employees", edges)
        body = mock_async_client._http_client.post.call_args[1]["json"]
        assert isinstance(body, list)
        assert len(body) == 2
        assert body[0] == {"from": 5, "to": 2, "type": "manager"}
        assert body[1] == {"from": 5, "to": 3, "type": "dotted_line", "metadata": {"project": "AI"}}

    @pytest.mark.asyncio
    async def test_create_edges_preserves_extra_fields(self, async_db, mock_async_client):
        """Extra fields should pass through, not be dropped."""
        mock_async_client._http_client.post = AsyncMock(return_value={"data": [], "total": 0})
        await async_db.create_edges("employees", [
            {"from": 1, "to": 2, "type": "manager", "weight": 0.8, "label": "reports_to"}
        ])
        body = mock_async_client._http_client.post.call_args[1]["json"]
        assert body[0]["weight"] == 0.8
        assert body[0]["label"] == "reports_to"

    @pytest.mark.asyncio
    async def test_update_edge_passes_body(self, async_db, mock_async_client):
        """JS SDK passes edge object directly to PATCH."""
        mock_async_client._http_client.patch = AsyncMock(return_value={"data": {}})
        await async_db.update_edge("employees", "9", {"from": 5, "to": 3, "type": "dotted_line"})
        body = mock_async_client._http_client.patch.call_args[1]["json"]
        assert body == {"from": 5, "to": 3, "type": "dotted_line"}

    @pytest.mark.asyncio
    async def test_update_edge_preserves_extra_fields(self, async_db, mock_async_client):
        mock_async_client._http_client.patch = AsyncMock(return_value={"data": {}})
        await async_db.update_edge("employees", 10, {
            "metadata": {"end_date": "2026-01-29"},
            "weight": 0.5,
        })
        body = mock_async_client._http_client.patch.call_args[1]["json"]
        assert body["weight"] == 0.5
        assert body["metadata"] == {"end_date": "2026-01-29"}

    @pytest.mark.asyncio
    async def test_delete_edges_sends_edge_ids(self, async_db, mock_async_client):
        """JS SDK sends { edge_ids: [...] }."""
        mock_async_client._http_client.delete = AsyncMock(return_value={"deleted": 2})
        await async_db.delete_edges("employees", [9, 10])
        body = mock_async_client._http_client.delete.call_args[1]["json"]
        assert body == {"edge_ids": [9, 10]}


# ============================================================================
# List Edges Query Params Tests
# ============================================================================

class TestListEdgesParams:

    @pytest.mark.asyncio
    async def test_list_edges_no_params(self, async_db, mock_async_client):
        mock_async_client._http_client.get = AsyncMock(return_value={"data": [], "total": 0})
        await async_db.list_edges("employees")
        params = mock_async_client._http_client.get.call_args[1]["params"]
        assert params["limit"] == 100
        assert params["offset"] == 0

    @pytest.mark.asyncio
    async def test_list_edges_with_filters(self, async_db, mock_async_client):
        mock_async_client._http_client.get = AsyncMock(return_value={"data": [], "total": 0})
        await async_db.list_edges("employees", from_id=[1, 2], types=["manager"], page=1, page_size=10)
        params = mock_async_client._http_client.get.call_args[1]["params"]
        assert params["from_id"] == [1, 2]
        assert params["types"] == ["manager"]
        assert params["page"] == 1
        assert params["page_size"] == 10


# ============================================================================
# Graph Query Builder Tests
# ============================================================================

class TestGraphQueryBuilder:
    """Verify graph traversal query params on QueryBuilder."""

    def test_format_sets_param(self, mock_sync_client):
        qb = QueryBuilder(mock_sync_client, "employees")
        qb.format("tree")
        params = qb.build_params()
        assert params["format"] == "tree"

    def test_include_sets_param(self, mock_sync_client):
        qb = QueryBuilder(mock_sync_client, "employees")
        qb.include("descendants")
        params = qb.build_params()
        assert params["include"] == "descendants"

    def test_depth_sets_param(self, mock_sync_client):
        qb = QueryBuilder(mock_sync_client, "employees")
        qb.depth(3)
        params = qb.build_params()
        assert params["depth"] == 3

    def test_types_sets_relationship_type(self, mock_sync_client):
        qb = QueryBuilder(mock_sync_client, "employees")
        qb.types(["manager", "dotted_line"])
        params = qb.build_params()
        assert params["relationship_type"] == ["manager", "dotted_line"]

    def test_chaining_graph_params(self, mock_sync_client):
        qb = (
            QueryBuilder(mock_sync_client, "employees")
            .filter("id", "eq", 1)
            .format("tree")
            .include("descendants")
            .depth(3)
            .types(["manager"])
        )
        params = qb.build_params()
        assert params["format"] == "tree"
        assert params["include"] == "descendants"
        assert params["depth"] == 3
        assert params["relationship_type"] == ["manager"]
        assert params["id"] == 1

    def test_graph_query_url(self, mock_sync_client):
        """Graph queries go to /data/ endpoint (same as regular queries)."""
        mock_sync_client._http_client.get = MagicMock(return_value={"data": [], "total": 0})
        qb = QueryBuilder(mock_sync_client, "employees")
        qb.format("tree").include("descendants").depth(3).execute()
        url = mock_sync_client._http_client.get.call_args[0][0]
        assert "/datatables/employees/data/" in url
