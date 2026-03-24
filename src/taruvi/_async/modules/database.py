"""
Database API Module

Provides methods for:
- Querying data tables
- Filtering, sorting, pagination
- CRUD operations on records
- Edge (relationship) management
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


# ============================================================================
# Shared Query Builder Logic
# ============================================================================

class _BaseQueryBuilder(BaseModule):
    """Base query builder with shared logic."""

    def __init__(self, http_client, config, table_name: str, app_slug: Optional[str] = None) -> None:
        super().__init__(http_client, config)
        self.app_slug = self._ensure_app_slug(app_slug)
        self.table_name = table_name
        self._filters: dict[str, Any] = {}
        self._sort_field: Optional[str] = None
        self._sort_order: str = "asc"
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

    def _add_filter(self, field: str, operator: str, value: Any) -> None:
        """Add a filter (shared logic)."""
        if operator == "eq":
            self._filters[field] = value
        else:
            self._filters[f"{field}__{operator}"] = value

    def _set_sort(self, field: str, order: str) -> None:
        """Set sort (shared logic)."""
        self._sort_field = field
        self._sort_order = order

    def _set_page_size(self, page_size: int) -> None:
        """Set page size (shared logic)."""
        self._page_size = page_size

    def _set_page(self, page: int) -> None:
        """Set page number (shared logic)."""
        self._page = page

    def _add_populate(self, *fields: str) -> None:
        """Add populate fields (shared logic)."""
        self._populate_fields.extend(fields)

    def _set_format(self, format_type: str) -> None:
        """Set response format (shared logic)."""
        self._format = format_type

    def _set_include(self, direction: str) -> None:
        """Set traversal direction (shared logic)."""
        self._include = direction

    def _set_depth(self, depth: int) -> None:
        """Set traversal depth (shared logic)."""
        self._depth = depth

    def _set_relationship_types(self, types: list[str]) -> None:
        """Set relationship types (shared logic)."""
        self._relationship_types = types

    def _add_aggregate(self, *expressions: str) -> None:
        """Add aggregate expressions (shared logic)."""
        self._aggregates.extend(expressions)

    def _set_group_by(self, *fields: str) -> None:
        """Set GROUP BY fields (shared logic)."""
        self._group_by = list(fields)

    def _set_having(self, condition: str) -> None:
        """Set HAVING condition (shared logic)."""
        self._having = condition

    def _set_search(self, query: str) -> None:
        """Set full-text search query (shared logic)."""
        self._search = query

    def build_params(self) -> dict[str, Any]:
        """Build query parameters for API request."""
        params = build_params_util(
            _sort=self._sort_field,
            _order=self._sort_order if self._sort_field else None,
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

        # Add relationship types (can be multiple)
        if self._relationship_types:
            for rel_type in self._relationship_types:
                params.setdefault("relationship_type", []).append(rel_type)

        # Merge filters
        params.update(self._filters)

        return params


class AsyncQueryBuilder(_BaseQueryBuilder):
    """Query builder for database operations."""

    def __init__(self, client: "AsyncClient", table_name: str, app_slug: Optional[str] = None) -> None:
        self.client = client
        super().__init__(client._http_client, client._config, table_name, app_slug)

    def filter(self, field: str, operator: str, value: Any) -> "AsyncQueryBuilder":
        """Add a filter to the query."""
        self._add_filter(field, operator, value)
        return self

    def search(self, query: str) -> "AsyncQueryBuilder":
        """Full-text search (requires search_vector field on table)."""
        self._set_search(query)
        return self

    def sort(self, field: str, order: str = "asc") -> "AsyncQueryBuilder":
        """Add sorting to the query."""
        self._set_sort(field, order)
        return self

    def page_size(self, page_size: int) -> "AsyncQueryBuilder":
        """Set number of records per page."""
        self._set_page_size(page_size)
        return self

    def page(self, page: int) -> "AsyncQueryBuilder":
        """Set page number (1-indexed)."""
        self._set_page(page)
        return self

    def populate(self, *fields: str) -> "AsyncQueryBuilder":
        """Populate related fields (foreign keys)."""
        self._add_populate(*fields)
        return self

    def format(self, format_type: str) -> "AsyncQueryBuilder":
        """Set response format: 'flat' (default), 'tree', or 'graph'."""
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

    def aggregate(self, *expressions: str) -> "AsyncQueryBuilder":
        """
        Add aggregate functions to the query.

        Args:
            expressions: Aggregate expressions like 'count(*)', 'sum(price)', 'avg(rating)'

        Returns:
            AsyncQueryBuilder for chaining

        Example:
            # Single aggregate
            result = await db.from_('orders').aggregate('sum(total)').execute()

            # Multiple aggregates
            result = await db.from_('products').aggregate('count(*)', 'avg(price)', 'sum(stock)').execute()
        """
        self._add_aggregate(*expressions)
        return self

    def group_by(self, *fields: str) -> "AsyncQueryBuilder":
        """
        Add GROUP BY clause for aggregations.

        Args:
            fields: Field names to group by

        Returns:
            AsyncQueryBuilder for chaining

        Example:
            # Group by single field
            result = await db.from_('orders') \\
                .aggregate('sum(total)', 'count(*)') \\
                .group_by('status') \\
                .execute()

            # Group by multiple fields
            result = await db.from_('sales') \\
                .aggregate('sum(amount)') \\
                .group_by('region', 'product_category') \\
                .execute()
        """
        self._set_group_by(*fields)
        return self

    def having(self, condition: str) -> "AsyncQueryBuilder":
        """
        Add HAVING clause to filter aggregated results.

        Args:
            condition: HAVING condition (e.g., 'sum_total > 1000')

        Returns:
            AsyncQueryBuilder for chaining

        Example:
            # Filter aggregated results
            result = await db.from_('orders') \\
                .aggregate('sum(total) as sum_total', 'count(*) as order_count') \\
                .group_by('customer_id') \\
                .having('sum_total > 1000') \\
                .execute()
        """
        self._set_having(condition)
        return self

    async def execute(self) -> dict[str, Any]:
        """Execute query and get results with metadata."""
        path = _DATATABLE_DATA.format(
            app_slug=self.app_slug,
            table_name=self.table_name
        )
        params = self.build_params()
        response = await self._http.get(path, params=params)
        
        return {
            "data": self._extract_data_list(response),
            "total": response.get("total", 0)
        }

    async def first(self) -> Optional[dict[str, Any]]:
        """Get first result."""
        result = await self.page_size(1).execute()
        return result['data'][0] if result['data'] else None

    async def count(self) -> int:
        """Get count of matching records."""
        path = _DATATABLE_DATA.format(
            app_slug=self.app_slug,
            table_name=self.table_name
        )
        params = self.build_params()
        params["_count"] = "true"
        response = await self._http.get(path, params=params)
        return response.get("total", 0)


class AsyncDatabaseModule(BaseModule):
    """Database API operations."""

    def __init__(self, client: "AsyncClient") -> None:
        """Initialize Database module."""
        self.client = client
        super().__init__(client._http_client, client._config)

    def from_(self, table_name: str, app_slug: Optional[str] = None) -> AsyncQueryBuilder:
        """Create a query builder for a table."""
        return AsyncQueryBuilder(self.client, table_name, app_slug)

    async def list_edges(
        self,
        table_name: str,
        *,
        from_id: Optional[list[int]] = None,
        to_id: Optional[list[int]] = None,
        types: Optional[list[str]] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        limit: Optional[int] = 100,
        offset: Optional[int] = 0,
        app_slug: Optional[str] = None,
    ) -> dict[str, Any]:
        """List edges (relationships) with filters."""
        app_slug = self._ensure_app_slug(app_slug)
        path = f"/api/apps/{app_slug}/datatables/{table_name}_edges/data/"

        params: dict[str, Any] = {}
        if from_id:
            for fid in from_id:
                params.setdefault("from_id", []).append(fid)
        if to_id:
            for tid in to_id:
                params.setdefault("to_id", []).append(tid)
        if types:
            for t in types:
                params.setdefault("types", []).append(t)
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["page_size"] = page_size
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        return await self._http.get(path, params=params)

    async def create_edges(
        self,
        table_name: str,
        edges: list[dict[str, Any]],
        *,
        app_slug: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create multiple edges (relationships) at once."""
        app_slug = self._ensure_app_slug(app_slug)
        path = f"/api/apps/{app_slug}/datatables/{table_name}_edges/data/"

        return await self._http.post(path, json=edges)

    async def delete_edges(
        self,
        table_name: str,
        edge_ids: list[int],
        *,
        app_slug: Optional[str] = None,
    ) -> dict[str, Any]:
        """Delete multiple edges (relationships) by IDs."""
        app_slug = self._ensure_app_slug(app_slug)
        path = f"/api/apps/{app_slug}/datatables/{table_name}_edges/data/"
        return await self._http.delete(path, json={"edge_ids": edge_ids})

    async def update_edge(
        self,
        table_name: str,
        edge_id: str | int,
        data: dict[str, Any],
        *,
        app_slug: Optional[str] = None,
    ) -> dict[str, Any]:
        """Update a single edge (relationship) by ID."""
        app_slug = self._ensure_app_slug(app_slug)
        path = f"/api/apps/{app_slug}/datatables/{table_name}_edges/data/{edge_id}/"

        return await self._http.patch(path, json=data)

    async def get(
        self,
        table_name: str,
        record_id: str | int,
        *,
        app_slug: Optional[str] = None,
    ) -> DatabaseRecord:
        """
        Get a single record by ID.

        Args:
            table_name: Name of the table
            record_id: Record ID
            app_slug: Optional app slug override

        Returns:
            DatabaseRecord dict with record data

        Example:
            record = await db.get('users', 123)
        """
        app_slug = self._ensure_app_slug(app_slug)
        path = _DATATABLE_RECORD.format(
            app_slug=app_slug,
            table_name=table_name,
            record_id=str(record_id)
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
        """
        Create single or multiple records.

        Args:
            table_name: Name of the table
            data: Single record (dict) or multiple records (list of dicts)
            app_slug: Optional app slug override

        Returns:
            DatabaseRecord dict if input was dict
            List of DatabaseRecord dicts if input was list

        Examples:
            # Single record
            record = await db.create('users', {'name': 'John', 'age': 30})

            # Bulk records
            records = await db.create('users', [
                {'name': 'Alice', 'age': 25},
                {'name': 'Bob', 'age': 35}
            ])
        """
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
        """
        Update single record by ID or multiple records in bulk.

        Args:
            table_name: Name of the table
            record_id:
                - For single update: Record ID (int/str)
                - For bulk update: List of dicts with 'id' field
            data: Update data (only for single record update)
            app_slug: Optional app slug override

        Returns:
            DatabaseRecord dict if single update
            List of DatabaseRecord dicts if bulk update

        Examples:
            # Single record update
            record = await db.update('users', 123, {'name': 'John Updated'})

            # Bulk record update
            records = await db.update('users', [
                {'id': 1, 'status': 'active'},
                {'id': 2, 'status': 'inactive'},
                {'id': 3, 'age': 25}
            ])
        """
        app_slug = self._ensure_app_slug(app_slug)

        # Detect single vs bulk update
        if isinstance(record_id, list):
            # Bulk update
            if data is not None:
                raise ValueError("data parameter not allowed for bulk update")
            path = _DATATABLE_DATA.format(app_slug=app_slug, table_name=table_name)
            response = await self._http.patch(path, json=record_id)
            return self._extract_data_list(response)
        else:
            # Single record update
            if data is None:
                raise ValueError("data is required for single record update")
            path = _DATATABLE_RECORD.format(
                app_slug=app_slug,
                table_name=table_name,
                record_id=str(record_id)
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
        """
        Delete single record by ID, multiple records by IDs, or records matching filter.

        Args:
            table_name: Name of the table
            record_id: Single record ID (for single delete)
            ids: List of record IDs (for bulk delete by IDs)
            filter: Filter dict (for bulk delete by filter)
            app_slug: Optional app slug override

        Returns:
            None for single delete
            Dict with deleted_count for bulk delete

        Examples:
            # Single record delete
            await db.delete('users', 123)

            # Bulk delete by IDs
            result = await db.delete('users', ids=[1, 2, 3])
            # Returns: {"deleted": 3, "message": "..."}

            # Bulk delete by filter
            result = await db.delete('users', filter={'status': 'inactive'})
            # Returns: {"deleted": 42, "message": "..."}
        """
        app_slug = self._ensure_app_slug(app_slug)

        # Validate exactly one delete method is provided
        methods_provided = sum([
            record_id is not None,
            ids is not None,
            filter is not None
        ])

        if methods_provided == 0:
            raise ValueError("Provide either record_id, ids, or filter parameter")
        if methods_provided > 1:
            raise ValueError("Provide only ONE of: record_id, ids, or filter")

        # Single record delete
        if record_id is not None:
            path = _DATATABLE_RECORD.format(
                app_slug=app_slug,
                table_name=table_name,
                record_id=str(record_id)
            )
            await self._http.delete(path)
            return None

        # Bulk delete by IDs or filter
        path = _DATATABLE_DATA.format(app_slug=app_slug, table_name=table_name)

        if ids is not None:
            # Delete by IDs - pass as query parameter
            ids_str = ','.join(str(id) for id in ids)
            response = await self._http.delete(path, params={"ids": ids_str})
            return response

        if filter is not None:
            # Delete by filter - pass as JSON query parameter
            import json
            filter_json = json.dumps(filter)
            response = await self._http.delete(path, params={"filter": filter_json})
            return response
