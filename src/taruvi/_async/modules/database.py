"""
Database API Module

Provides methods for:
- Querying data tables
- Filtering, sorting, pagination
- CRUD operations on records
- Edge (relationship) management via .edges()
- Graph/tree queries
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from taruvi.modules.base import BaseModule
from taruvi.utils import build_params as build_params_util
from taruvi.types import DatabaseRecord

if TYPE_CHECKING:
    from taruvi._async.client import AsyncClient

# API endpoint paths for database
_DATATABLE_DATA = "/api/apps/{app_slug}/datatables/{table_name}/data/"
_DATATABLE_RECORD = "/api/apps/{app_slug}/datatables/{table_name}/data/{record_id}/"
_DATATABLE_UPSERT = "/api/apps/{app_slug}/datatables/{table_name}/data/upsert/"

# Operators whose values must be comma-joined when passed as list/tuple.
# httpx serializes Python lists as repeated keys, but Django QueryDict.dict()
# keeps only the last value — so we must send comma-separated strings.
_LIST_OPERATORS = frozenset({
    "in", "nin", "ina", "nina",
    "between", "nbetween",
    "acontains", "nacontains", "acontainedby", "nacontainedby",
    "aoverlap", "naoverlap",
    "rcontains", "rcontainedby", "roverlaps",
    "radjacent", "rstrictleft", "rstrictright",
})


# ============================================================================
# Shared Query Builder Logic
# ============================================================================

class _BaseQueryBuilder(BaseModule):
    """Base query builder with shared logic."""

    def __init__(self, http_client, config, table_name: str, app_slug: Optional[str] = None) -> None:
        super().__init__(http_client, config)
        self.app_slug = self._ensure_app_slug(app_slug)
        self.table_name = table_name
        self._is_edges: bool = False
        self._record_id: Optional[str] = None
        self._operation: Optional[str] = None
        self._body: Any = None
        self._delete_ids: Optional[list[int]] = None
        self._is_upsert: bool = False
        self._unique_fields: Optional[str] = None
        self._filters: dict[str, Any] = {}
        self._ordering_parts: list[str] = []
        self._page_size: Optional[int] = None
        self._page: int = 1
        self._populate_fields: list[str] = []
        self._format: Optional[str] = None
        self._include: Optional[str] = None
        self._depth: Optional[int] = None
        self._relationship_types: list[str] = []
        self._aggregates: list[str] = []
        self._group_by: list[str] = []
        self._having: Optional[str] = None
        self._search: Optional[str] = None
        self._raw_filters: Optional[str] = None

    def _get_table_name(self) -> str:
        return f"{self.table_name}_edges" if self._is_edges else self.table_name

    def _add_filter(self, field: str, operator: str, value: Any) -> None:
        if isinstance(value, (list, tuple)) and operator in _LIST_OPERATORS:
            value = ",".join(str(v) for v in value)
        if operator == "eq":
            self._filters[field] = value
        else:
            self._filters[f"{field}__{operator}"] = value

    def _set_sort(self, field: str, order: str) -> None:
        ordering = f"-{field}" if order == "desc" else field
        self._ordering_parts = [ordering]

    def _add_sort(self, field: str, order: str) -> None:
        ordering = f"-{field}" if order == "desc" else field
        self._ordering_parts.append(ordering)

    def _set_page_size(self, page_size: int) -> None:
        self._page_size = page_size

    def _set_page(self, page: int) -> None:
        self._page = page

    def _add_populate(self, *fields: str) -> None:
        self._populate_fields.extend(fields)

    def _set_format(self, format_type: str) -> None:
        self._format = format_type

    def _set_include(self, direction: str) -> None:
        self._include = direction

    def _set_depth(self, depth: int) -> None:
        self._depth = depth

    def _set_relationship_types(self, types: list[str]) -> None:
        self._relationship_types = types

    def _add_aggregate(self, *expressions: str) -> None:
        self._aggregates.extend(expressions)

    def _set_group_by(self, *fields: str) -> None:
        self._group_by = list(fields)

    def _set_having(self, condition: str) -> None:
        self._having = condition

    def _set_search(self, query: str) -> None:
        self._search = query

    def _set_raw_filters(self, filters: dict | list) -> None:
        import json
        self._raw_filters = json.dumps(filters)

    def build_params(self) -> dict[str, Any]:
        """Build query parameters for API request."""
        ordering = ",".join(self._ordering_parts) if self._ordering_parts else None
        params = build_params_util(
            ordering=ordering,
            page_size=self._page_size,
            page=self._page if self._page != 1 else None,
            populate=",".join(self._populate_fields) if self._populate_fields else None,
            format=self._format,
            include=self._include,
            depth=self._depth,
            _aggregate=",".join(self._aggregates) if self._aggregates else None,
            _group_by=",".join(self._group_by) if self._group_by else None,
            _having=self._having,
            search=self._search,
        )

        if self._relationship_types:
            for rel_type in self._relationship_types:
                params.setdefault("relationship_type", []).append(rel_type)

        if self._raw_filters:
            params["filters"] = self._raw_filters
        else:
            params.update(self._filters)
        return params


class AsyncQueryBuilder(_BaseQueryBuilder):
    """Query builder for database operations."""

    def __init__(self, client: "AsyncClient", table_name: str, app_slug: Optional[str] = None) -> None:
        self.client = client
        super().__init__(client._http_client, client._config, table_name, app_slug)

    # -- Edge toggle --

    def edges(self) -> "AsyncQueryBuilder":
        """Target the edges table (e.g., employees → employees_edges)."""
        self._is_edges = True
        return self

    # -- CRUD setters (lazy — actual request happens in execute()) --

    def get(self, record_id: str | int) -> "AsyncQueryBuilder":
        """Set record ID for GET or as target for update/delete."""
        self._record_id = str(record_id)
        return self

    def create(self, body: dict[str, Any] | list[dict[str, Any]]) -> "AsyncQueryBuilder":
        """Stage a POST (create) operation."""
        self._operation = "POST"
        self._body = body
        return self

    def update(self, body: dict[str, Any] | list[dict[str, Any]]) -> "AsyncQueryBuilder":
        """Stage a PATCH (update) operation. Call .get(id) first for single record."""
        self._operation = "PATCH"
        self._body = body
        return self

    def delete(self, record_id_or_ids: str | int | list[int] | None = None) -> "AsyncQueryBuilder":
        """Stage a DELETE operation. Pass int[] for bulk edge delete, str/int for single record."""
        self._operation = "DELETE"
        if isinstance(record_id_or_ids, list):
            self._delete_ids = record_id_or_ids
        elif record_id_or_ids is not None:
            self._record_id = str(record_id_or_ids)
        return self

    def upsert(self, body: dict[str, Any] | list[dict[str, Any]], *, unique_fields: list[str] | None = None) -> "AsyncQueryBuilder":
        """Stage an upsert (insert or update) operation."""
        self._operation = "POST"
        self._body = body
        self._is_upsert = True
        if unique_fields:
            self._unique_fields = ",".join(unique_fields)
        return self

    # -- Filter & query methods --

    def filter(self, field_or_logic: str | dict | list, operator: str | None = None, value: Any = None) -> "AsyncQueryBuilder":
        """Filter records. Supports simple and complex filters.

        Simple: .filter("age", "gte", 30)
        Complex: .filter({"or": [{"department": "eng"}, {"department": "hr"}]})
        """
        if isinstance(field_or_logic, (dict, list)):
            self._set_raw_filters(field_or_logic)
        else:
            self._add_filter(field_or_logic, operator, value)
        return self

    def search(self, query: str) -> "AsyncQueryBuilder":
        self._set_search(query)
        return self

    def sort(self, field: str, order: str = "asc") -> "AsyncQueryBuilder":
        self._set_sort(field, order)
        return self

    def order_by(self, *fields: tuple[str, str] | str) -> "AsyncQueryBuilder":
        """Multi-sort: order_by(("salary", "desc"), ("name", "asc")) or order_by("-salary", "name")."""
        self._ordering_parts = []
        for f in fields:
            if isinstance(f, (list, tuple)):
                self._add_sort(f[0], f[1] if len(f) > 1 else "asc")
            elif isinstance(f, str):
                if f.startswith("-"):
                    self._add_sort(f[1:], "desc")
                else:
                    self._add_sort(f, "asc")
        return self

    def page_size(self, page_size: int) -> "AsyncQueryBuilder":
        self._set_page_size(page_size)
        return self

    def page(self, page: int) -> "AsyncQueryBuilder":
        self._set_page(page)
        return self

    def populate(self, *fields: str) -> "AsyncQueryBuilder":
        self._add_populate(*fields)
        return self

    # -- Graph traversal methods --

    def format(self, format_type: str) -> "AsyncQueryBuilder":
        """Set response format: 'tree' or 'graph'."""
        self._set_format(format_type)
        return self

    def include(self, direction: str) -> "AsyncQueryBuilder":
        """Set traversal direction: 'descendants', 'ancestors', or 'both'."""
        self._set_include(direction)
        return self

    def depth(self, depth: int) -> "AsyncQueryBuilder":
        """Set maximum traversal depth."""
        self._set_depth(depth)
        return self

    def types(self, relationship_types: list[str]) -> "AsyncQueryBuilder":
        """Filter by relationship types (e.g., ['manager', 'dotted_line'])."""
        self._set_relationship_types(relationship_types)
        return self

    # -- Aggregation methods --

    def aggregate(self, *expressions: str) -> "AsyncQueryBuilder":
        """Add aggregate functions (e.g., 'count(*)', 'sum(price)')."""
        self._add_aggregate(*expressions)
        return self

    def group_by(self, *fields: str) -> "AsyncQueryBuilder":
        """Add GROUP BY clause for aggregations."""
        self._set_group_by(*fields)
        return self

    def having(self, condition: str) -> "AsyncQueryBuilder":
        """Add HAVING clause to filter aggregated results."""
        self._set_having(condition)
        return self

    # -- Execution --

    def _build_path(self) -> str:
        table = self._get_table_name()
        if self._is_upsert:
            return _DATATABLE_UPSERT.format(app_slug=self.app_slug, table_name=table)
        if self._record_id:
            return _DATATABLE_RECORD.format(
                app_slug=self.app_slug, table_name=table, record_id=self._record_id
            )
        return _DATATABLE_DATA.format(app_slug=self.app_slug, table_name=table)

    async def execute(self) -> dict[str, Any]:
        """Execute the staged operation (GET/POST/PATCH/DELETE)."""
        path = self._build_path()
        params = self.build_params()
        op = self._operation or "GET"

        if op == "POST":
            post_params = {}
            if self._unique_fields:
                post_params["unique_fields"] = self._unique_fields
            return await self._http.post(path, json=self._body, params=post_params or None)
        if op == "PATCH":
            if not self._record_id and not isinstance(self._body, list):
                raise ValueError("PATCH requires a record ID. Call .get(id) first.")
            return await self._http.patch(path, json=self._body)
        if op == "DELETE":
            if self._delete_ids:
                ids_param = ",".join(str(i) for i in self._delete_ids)
                return await self._http.delete(path, params={"ids": ids_param})
            if self._body:
                return await self._http.delete(path, json=self._body)
            return await self._http.delete(path)

        # Default: GET
        response = await self._http.get(path, params=params)
        return {
            "data": self._extract_data_list(response),
            "total": response.get("total", 0)
        }

    async def first(self) -> Optional[dict[str, Any]]:
        """Get first result."""
        result = await self.page_size(1).execute()
        data = result.get("data", [])
        if isinstance(data, list):
            return data[0] if data else None
        return data

    async def count(self) -> int:
        """Get count of matching records."""
        path = self._build_path()
        params = self.build_params()
        params["_count"] = "true"
        response = await self._http.get(path, params=params)
        return response.get("total", 0)


class AsyncDatabaseModule(BaseModule):
    """Database API operations."""

    def __init__(self, client: "AsyncClient") -> None:
        self.client = client
        super().__init__(client._http_client, client._config)

    def from_(self, table_name: str, app_slug: Optional[str] = None) -> AsyncQueryBuilder:
        """Create a query builder for a table."""
        return AsyncQueryBuilder(self.client, table_name, app_slug)

    async def get(
        self,
        table_name: str,
        record_id: str | int,
        *,
        app_slug: Optional[str] = None,
    ) -> DatabaseRecord:
        """Get a single record by ID."""
        app_slug = self._ensure_app_slug(app_slug)
        path = _DATATABLE_RECORD.format(
            app_slug=app_slug, table_name=table_name, record_id=str(record_id)
        )
        response = await self._http.get(path)
        return self._extract_data(response)

    async def create(
        self,
        table_name: str,
        data: dict[str, Any] | list[dict[str, Any]],
        *,
        app_slug: Optional[str] = None,
    ) -> DatabaseRecord | list[DatabaseRecord]:
        """Create single or multiple records."""
        app_slug = self._ensure_app_slug(app_slug)
        path = _DATATABLE_DATA.format(app_slug=app_slug, table_name=table_name)
        response = await self._http.post(path, json=data)
        return response.get("data")

    async def update(
        self,
        table_name: str,
        record_id: str | int | list[dict[str, Any]],
        data: Optional[dict[str, Any]] = None,
        *,
        app_slug: Optional[str] = None,
    ) -> DatabaseRecord | list[DatabaseRecord]:
        """Update single record by ID or multiple records in bulk."""
        app_slug = self._ensure_app_slug(app_slug)

        if isinstance(record_id, list):
            if data is not None:
                raise ValueError("data parameter not allowed for bulk update")
            path = _DATATABLE_DATA.format(app_slug=app_slug, table_name=table_name)
            response = await self._http.patch(path, json=record_id)
            return self._extract_data_list(response)
        else:
            if data is None:
                raise ValueError("data is required for single record update")
            path = _DATATABLE_RECORD.format(
                app_slug=app_slug, table_name=table_name, record_id=str(record_id)
            )
            response = await self._http.patch(path, json=data)
            return self._extract_data(response)

    async def delete(
        self,
        table_name: str,
        record_id: Optional[str | int] = None,
        *,
        ids: Optional[list[int]] = None,
        filter: Optional[dict[str, Any]] = None,
        app_slug: Optional[str] = None,
    ) -> None | dict[str, Any]:
        """Delete single record by ID, multiple by IDs, or by filter."""
        app_slug = self._ensure_app_slug(app_slug)

        methods_provided = sum([
            record_id is not None,
            ids is not None,
            filter is not None
        ])
        if methods_provided == 0:
            raise ValueError("Provide either record_id, ids, or filter parameter")
        if methods_provided > 1:
            raise ValueError("Provide only ONE of: record_id, ids, or filter")

        if record_id is not None:
            path = _DATATABLE_RECORD.format(
                app_slug=app_slug, table_name=table_name, record_id=str(record_id)
            )
            await self._http.delete(path)
            return None

        path = _DATATABLE_DATA.format(app_slug=app_slug, table_name=table_name)

        if ids is not None:
            ids_str = ','.join(str(id) for id in ids)
            return await self._http.delete(path, params={"ids": ids_str})

        if filter is not None:
            import json
            return await self._http.delete(path, params={"filter": json.dumps(filter)})
