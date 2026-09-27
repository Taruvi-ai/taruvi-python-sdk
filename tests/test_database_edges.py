"""Unit tests for database edge CRUD and graph query builder methods."""

import json
from unittest.mock import AsyncMock, MagicMock
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


# ============================================================================
# Edge URL Tests — .edges() appends _edges to table name
# ============================================================================

class TestEdgeURLs:

    @pytest.mark.asyncio
    async def test_edges_list_url(self, mock_async_client):
        mock_async_client._http_client.get = AsyncMock(return_value={"data": [], "total": 0})
        await AsyncQueryBuilder(mock_async_client, "employees").edges().execute()
        url = mock_async_client._http_client.get.call_args[0][0]
        assert url == "/api/apps/test-app/datatables/employees_edges/data/"

    @pytest.mark.asyncio
    async def test_edges_create_url(self, mock_async_client):
        mock_async_client._http_client.post = AsyncMock(return_value={"data": [], "total": 0})
        await AsyncQueryBuilder(mock_async_client, "employees").edges().create([
            {"from_id": 1, "to_id": 2, "type": "manager"}
        ]).execute()
        url = mock_async_client._http_client.post.call_args[0][0]
        assert url == "/api/apps/test-app/datatables/employees_edges/data/"

    @pytest.mark.asyncio
    async def test_edges_update_url(self, mock_async_client):
        mock_async_client._http_client.patch = AsyncMock(return_value={"data": {}})
        await AsyncQueryBuilder(mock_async_client, "employees").edges().get("9").update(
            {"type": "dotted_line"}
        ).execute()
        url = mock_async_client._http_client.patch.call_args[0][0]
        assert url == "/api/apps/test-app/datatables/employees_edges/data/9/"

    @pytest.mark.asyncio
    async def test_edges_delete_url(self, mock_async_client):
        mock_async_client._http_client.delete = AsyncMock(return_value={"deleted": 2})
        await AsyncQueryBuilder(mock_async_client, "employees").edges().delete([9, 10]).execute()
        url = mock_async_client._http_client.delete.call_args[0][0]
        assert url == "/api/apps/test-app/datatables/employees_edges/data/"

    def test_sync_edges_list_url(self, mock_sync_client):
        mock_sync_client._http_client.get = MagicMock(return_value={"data": [], "total": 0})
        QueryBuilder(mock_sync_client, "employees").edges().execute()
        url = mock_sync_client._http_client.get.call_args[0][0]
        assert url == "/api/apps/test-app/datatables/employees_edges/data/"

    def test_sync_edges_create_url(self, mock_sync_client):
        mock_sync_client._http_client.post = MagicMock(return_value={"data": [], "total": 0})
        QueryBuilder(mock_sync_client, "employees").edges().create([
            {"from_id": 1, "to_id": 2, "type": "manager"}
        ]).execute()
        url = mock_sync_client._http_client.post.call_args[0][0]
        assert url == "/api/apps/test-app/datatables/employees_edges/data/"

    @pytest.mark.asyncio
    async def test_edges_does_not_affect_non_edge_queries(self, mock_async_client):
        """Calling .edges() on one builder doesn't affect another."""
        mock_async_client._http_client.get = AsyncMock(return_value={"data": [], "total": 0})
        base = AsyncDatabaseModule(mock_async_client)
        await base.from_("employees").edges().execute()
        await base.from_("employees").execute()
        calls = mock_async_client._http_client.get.call_args_list
        assert "employees_edges" in calls[0][0][0]
        assert "employees_edges" not in calls[1][0][0]


# ============================================================================
# Edge Request Body Tests
# ============================================================================

class TestEdgeRequestBody:

    @pytest.mark.asyncio
    async def test_create_passes_body_as_array(self, mock_async_client):
        mock_async_client._http_client.post = AsyncMock(return_value={"data": [], "total": 0})
        edges = [
            {"from_id": 5, "to_id": 2, "type": "manager"},
            {"from_id": 5, "to_id": 3, "type": "dotted_line", "metadata": {"project": "AI"}},
        ]
        await AsyncQueryBuilder(mock_async_client, "employees").edges().create(edges).execute()
        body = mock_async_client._http_client.post.call_args[1]["json"]
        assert isinstance(body, list)
        assert len(body) == 2
        assert body[0] == {"from_id": 5, "to_id": 2, "type": "manager"}

    @pytest.mark.asyncio
    async def test_create_preserves_extra_fields(self, mock_async_client):
        mock_async_client._http_client.post = AsyncMock(return_value={"data": [], "total": 0})
        await AsyncQueryBuilder(mock_async_client, "employees").edges().create([
            {"from_id": 1, "to_id": 2, "type": "manager", "weight": 0.8}
        ]).execute()
        body = mock_async_client._http_client.post.call_args[1]["json"]
        assert body[0]["weight"] == 0.8

    @pytest.mark.asyncio
    async def test_update_passes_body(self, mock_async_client):
        mock_async_client._http_client.patch = AsyncMock(return_value={"data": {}})
        await AsyncQueryBuilder(mock_async_client, "employees").edges().get("9").update(
            {"from_id": 5, "to_id": 3, "type": "dotted_line"}
        ).execute()
        body = mock_async_client._http_client.patch.call_args[1]["json"]
        assert body == {"from_id": 5, "to_id": 3, "type": "dotted_line"}

    @pytest.mark.asyncio
    async def test_delete_sends_edge_ids(self, mock_async_client):
        mock_async_client._http_client.delete = AsyncMock(return_value={"deleted": 2})
        await AsyncQueryBuilder(mock_async_client, "employees").edges().delete([9, 10]).execute()
        params = mock_async_client._http_client.delete.call_args[1]["params"]
        assert params == {"ids": "9,10"}

    @pytest.mark.asyncio
    async def test_delete_filtered_sends_filter_object(self, mock_async_client):
        mock_async_client._http_client.delete = AsyncMock(return_value={"deleted": 2})
        await (
            AsyncQueryBuilder(mock_async_client, "employees")
            .filter("status", "eq", "archived")
            .filter("id", "in", [1, 2])
            .delete_filtered()
            .execute()
        )
        params = mock_async_client._http_client.delete.call_args[1]["params"]
        assert json.loads(params["filter"]) == {"status": "archived", "id__in": "1,2"}

    @pytest.mark.asyncio
    async def test_delete_filtered_wraps_filter_tree(self, mock_async_client):
        mock_async_client._http_client.delete = AsyncMock(return_value={"deleted": 1})
        tree = {"or": [{"status": "archived"}, {"status": "draft"}]}
        await (
            AsyncQueryBuilder(mock_async_client, "employees")
            .filter(tree)
            .delete_filtered()
            .execute()
        )
        params = mock_async_client._http_client.delete.call_args[1]["params"]
        sent = json.loads(params["filter"])
        assert json.loads(sent["filters"]) == tree

    @pytest.mark.asyncio
    async def test_delete_filtered_without_filters_raises(self, mock_async_client):
        mock_async_client._http_client.delete = AsyncMock(return_value={})
        with pytest.raises(ValueError, match="requires at least one filter"):
            await AsyncQueryBuilder(mock_async_client, "employees").delete_filtered().execute()
        mock_async_client._http_client.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_filtered_refuses_search_instead_of_widening(self, mock_async_client):
        mock_async_client._http_client.delete = AsyncMock(return_value={})
        with pytest.raises(ValueError, match="can't narrow a delete by search"):
            await (
                AsyncQueryBuilder(mock_async_client, "employees")
                .search("needle")
                .filter("status", "eq", "archived")
                .delete_filtered()
                .execute()
            )
        mock_async_client._http_client.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_filtered_refuses_pagination(self, mock_async_client):
        mock_async_client._http_client.delete = AsyncMock(return_value={})
        with pytest.raises(ValueError, match="page, page_size"):
            await (
                AsyncQueryBuilder(mock_async_client, "employees")
                .filter("status", "eq", "archived")
                .page(2)
                .page_size(10)
                .delete_filtered()
                .execute()
            )
        mock_async_client._http_client.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_first_keeps_the_requested_page(self, mock_async_client):
        mock_async_client._http_client.get = AsyncMock(return_value={"data": [{"id": 21}, {"id": 22}], "total": 40})
        builder = AsyncQueryBuilder(mock_async_client, "employees").page(2).page_size(20)
        row = await builder.first()
        params = mock_async_client._http_client.get.call_args[1]["params"]
        assert params["page"] == 2 and params["page_size"] == 20
        assert row == {"id": 21}

    @pytest.mark.asyncio
    async def test_first_requests_one_row_without_changing_the_builder(self, mock_async_client):
        mock_async_client._http_client.get = AsyncMock(return_value={"data": [{"id": 1}], "total": 5})
        builder = AsyncQueryBuilder(mock_async_client, "employees").page_size(50)
        await builder.first()
        assert mock_async_client._http_client.get.call_args[1]["params"]["page_size"] == 1
        assert builder._page_size == 50

    @pytest.mark.asyncio
    async def test_delete_single_record(self, mock_async_client):
        mock_async_client._http_client.delete = AsyncMock(return_value={})
        await AsyncQueryBuilder(mock_async_client, "employees").edges().delete("9").execute()
        url = mock_async_client._http_client.delete.call_args[0][0]
        assert url == "/api/apps/test-app/datatables/employees_edges/data/9/"

    @pytest.mark.asyncio
    async def test_patch_without_record_id_raises(self, mock_async_client):
        with pytest.raises(ValueError, match="record ID"):
            await AsyncQueryBuilder(mock_async_client, "employees").update({"name": "x"}).execute()


# ============================================================================
# Graph Query Builder Tests
# ============================================================================

class TestGraphQueryBuilder:

    def test_format_sets_param(self, mock_sync_client):
        params = QueryBuilder(mock_sync_client, "employees").format("tree").build_params()
        assert params["format"] == "tree"

    def test_include_sets_param(self, mock_sync_client):
        params = QueryBuilder(mock_sync_client, "employees").include("descendants").build_params()
        assert params["include"] == "descendants"

    def test_depth_sets_param(self, mock_sync_client):
        params = QueryBuilder(mock_sync_client, "employees").depth(3).build_params()
        assert params["depth"] == 3

    def test_types_sets_relationship_type(self, mock_sync_client):
        params = QueryBuilder(mock_sync_client, "employees").types(["manager", "dotted_line"]).build_params()
        assert params["relationship_type"] == ["manager", "dotted_line"]

    def test_chaining_graph_params(self, mock_sync_client):
        params = (
            QueryBuilder(mock_sync_client, "employees")
            .filter("id", "eq", 1)
            .format("tree")
            .include("descendants")
            .depth(3)
            .types(["manager"])
            .build_params()
        )
        assert params["format"] == "tree"
        assert params["include"] == "descendants"
        assert params["depth"] == 3
        assert params["relationship_type"] == ["manager"]
        assert params["id"] == 1

    def test_graph_query_url(self, mock_sync_client):
        mock_sync_client._http_client.get = MagicMock(return_value={"data": [], "total": 0})
        QueryBuilder(mock_sync_client, "employees").format("tree").include("descendants").depth(3).execute()
        url = mock_sync_client._http_client.get.call_args[0][0]
        assert "/datatables/employees/data/" in url


# ============================================================================
# QueryBuilder CRUD on regular tables
# ============================================================================

class TestQueryBuilderCRUD:

    @pytest.mark.asyncio
    async def test_create_on_regular_table(self, mock_async_client):
        mock_async_client._http_client.post = AsyncMock(return_value={"data": {"id": 1}})
        await AsyncQueryBuilder(mock_async_client, "users").create({"name": "Alice"}).execute()
        url = mock_async_client._http_client.post.call_args[0][0]
        assert url == "/api/apps/test-app/datatables/users/data/"

    @pytest.mark.asyncio
    async def test_get_single_record(self, mock_async_client):
        mock_async_client._http_client.get = AsyncMock(return_value={"data": {"id": 1}, "total": 0})
        await AsyncQueryBuilder(mock_async_client, "users").get("123").execute()
        url = mock_async_client._http_client.get.call_args[0][0]
        assert url == "/api/apps/test-app/datatables/users/data/123/"

    @pytest.mark.asyncio
    async def test_update_single_record(self, mock_async_client):
        mock_async_client._http_client.patch = AsyncMock(return_value={"data": {}})
        await AsyncQueryBuilder(mock_async_client, "users").get("123").update({"name": "Bob"}).execute()
        url = mock_async_client._http_client.patch.call_args[0][0]
        assert url == "/api/apps/test-app/datatables/users/data/123/"

    @pytest.mark.asyncio
    async def test_delete_single_record(self, mock_async_client):
        mock_async_client._http_client.delete = AsyncMock(return_value={})
        await AsyncQueryBuilder(mock_async_client, "users").delete("123").execute()
        url = mock_async_client._http_client.delete.call_args[0][0]
        assert url == "/api/apps/test-app/datatables/users/data/123/"


class TestFilterTreeWithFlatFilters:

    def test_list_read_sends_flat_filters_and_tree(self, mock_sync_client):
        qb = QueryBuilder(mock_sync_client, "tasks").filter("owner", "eq", "ada").filter(
            {"or": [{"status": "open"}, {"status": "blocked"}]}
        )
        params = qb.build_params()
        assert params["owner"] == "ada"
        assert json.loads(params["filters"]) == {"or": [{"status": "open"}, {"status": "blocked"}]}

    @pytest.mark.asyncio
    async def test_filtered_delete_sends_flat_filters_and_tree(self, mock_async_client):
        mock_async_client._http_client.delete = AsyncMock(return_value={"deleted_count": 1})
        await (
            AsyncQueryBuilder(mock_async_client, "tasks")
            .filter("owner", "eq", "ada")
            .filter({"or": [{"status": "open"}]})
            .delete_filtered()
            .execute()
        )
        sent = json.loads(mock_async_client._http_client.delete.call_args[1]["params"]["filter"])
        assert sent["owner"] == "ada"
        assert json.loads(sent["filters"]) == {"or": [{"status": "open"}]}
