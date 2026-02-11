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
    from taruvi._sync.client import SyncClient

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
        )

        # Add relationship types (can be multiple)
        if self._relationship_types:
            for rel_type in self._relationship_types:
                params.setdefault("relationship_type", []).append(rel_type)

        # Merge filters
        params.update(self._filters)

        return params


class QueryBuilder(_BaseQueryBuilder):
    """Query builder for database operations."""

    def __init__(self, client: "SyncClient", table_name: str, app_slug: Optional[str] = None) -> None:
        self.client = client
        super().__init__(client._http_client, client._config, table_name, app_slug)

    def filter(self, field: str, operator: str, value: Any) -> "QueryBuilder":
        """Add a filter to the query."""
        self._add_filter(field, operator, value)
        return self

    def sort(self, field: str, order: str = "asc") -> "QueryBuilder":
        """Add sorting to the query."""
        self._set_sort(field, order)
        return self

    def page_size(self, page_size: int) -> "QueryBuilder":
        """Set number of records per page."""
        self._set_page_size(page_size)
        return self

    def page(self, page: int) -> "QueryBuilder":
        """Set page number (1-indexed)."""
        self._set_page(page)
        return self

    def populate(self, *fields: str) -> "QueryBuilder":
        """Populate related fields (foreign keys)."""
        self._add_populate(*fields)
        return self

    def format(self, format_type: str) -> "QueryBuilder":
        """
        Set response format for hierarchical/graph data.

        Args:
            format_type: Response format - 'flat' (default), 'tree', or 'graph'

        Returns:
            QueryBuilder for chaining

        Example:
            # Get data in tree format
            tree = db.query('categories').format('tree').get()

            # Get data in graph format
            graph = db.query('categories').format('graph').get()
        """
        self._set_format(format_type)
        return self

    def include(self, direction: str) -> "QueryBuilder":
        """
        Set traversal direction for graph/tree queries.

        Args:
            direction: Traversal direction - 'descendants', 'ancestors', or 'both'

        Returns:
            QueryBuilder for chaining

        Example:
            # Get node and all descendants
            nodes = db.query('categories') \\
                .filter('id', 'eq', 5) \\
                .include('descendants') \\
                .get()
        """
        self._set_include(direction)
        return self

    def depth(self, depth: int) -> "QueryBuilder":
        """
        Set maximum traversal depth for graph/tree queries.

        Args:
            depth: Maximum depth to traverse (e.g., 3 for 3 levels)

        Returns:
            QueryBuilder for chaining

        Example:
            # Get node and 3 levels of descendants
            nodes = db.query('categories') \\
                .filter('id', 'eq', 5) \\
                .include('descendants') \\
                .depth(3) \\
                .get()
        """
        self._set_depth(depth)
        return self

    def relationship_types(self, types: list[str]) -> "QueryBuilder":
        """
        Filter by relationship types for multi-type graphs.

        Args:
            types: List of relationship types to include (e.g., ['manager', 'dotted_line'])

        Returns:
            QueryBuilder for chaining

        Example:
            # Get only manager and dotted_line relationships
            nodes = db.query('employees') \\
                .relationship_types(['manager', 'dotted_line']) \\
                .include('descendants') \\
                .get()
        """
        self._set_relationship_types(types)
        return self

    def get(self) -> list[dict[str, Any]]:
        """Execute query and get results."""
        path = _DATATABLE_DATA.format(
            app_slug=self.app_slug,
            table_name=self.table_name
        )
        params = self.build_params()
        response = self._http.get(path, params=params)
        return self._extract_data_list(response)

    def first(self) -> Optional[dict[str, Any]]:
        """Get first result."""
        results = self.page_size(1).get()
        return results[0] if results else None

    def count(self) -> int:
        """Get count of matching records."""
        path = _DATATABLE_DATA.format(
            app_slug=self.app_slug,
            table_name=self.table_name
        )
        params = self.build_params()
        params["_count"] = "true"
        response = self._http.get(path, params=params)
        return response.get("total", 0)


class DatabaseModule(BaseModule):
    """Database API operations."""

    def __init__(self, client: "SyncClient") -> None:
        """Initialize Database module."""
        self.client = client
        super().__init__(client._http_client, client._config)

    def query(self, table_name: str, app_slug: Optional[str] = None) -> QueryBuilder:
        """Create a query builder for a table."""
        return QueryBuilder(self.client, table_name, app_slug)

    def list_edges(
        self,
        table_name: str,
        *,
        from_id: Optional[list[int]] = None,
        to_id: Optional[list[int]] = None,
        types: Optional[list[str]] = None,
        limit: int = 100,
        offset: int = 0,
        app_slug: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        List edges (relationships) with filters.

        Args:
            table_name: Name of the table
            from_id: Filter by source node ID(s)
            to_id: Filter by target node ID(s)
            types: Filter by relationship types
            limit: Maximum number of edges to return
            offset: Offset for pagination
            app_slug: Optional app slug override

        Returns:
            Dict with 'edges' list and 'total' count:
            {
                "edges": [
                    {"id": 1, "from_id": 5, "to_id": 10, "type": "manager", "metadata": {...}},
                    ...
                ],
                "total": 42
            }

        Example:
            edges = db.list_edges(
                'employees',
                from_id=[1, 2],
                types=['manager', 'dotted_line'],
                limit=10
            )
        """
        app_slug = self._ensure_app_slug(app_slug)
        path = f"/api/apps/{app_slug}/datatables/{table_name}/edges/"

        params = {}
        if from_id:
            for fid in from_id:
                params.setdefault("from_id", []).append(fid)
        if to_id:
            for tid in to_id:
                params.setdefault("to_id", []).append(tid)
        if types:
            for t in types:
                params.setdefault("types", []).append(t)
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        response = self._http.get(path, params=params)
        return response

    def create_edges(
        self,
        table_name: str,
        edges: list[dict[str, Any]],
        *,
        app_slug: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Create multiple edges (relationships) at once.

        Args:
            table_name: Name of the table
            edges: List of edge dicts with 'from_id', 'to_id', 'type', and optional 'metadata'
            app_slug: Optional app slug override

        Returns:
            Dict with 'data' list and 'total' count:
            {
                "data": [
                    {"id": 1, "from_id": 5, "to_id": 10, "type": "manager", "metadata": {...}},
                    ...
                ],
                "total": 3,
                "message": "Edges created successfully"
            }

        Example:
            result = db.create_edges('employees', [
                {'from_id': 1, 'to_id': 2, 'type': 'manager', 'metadata': {'primary': True}},
                {'from_id': 1, 'to_id': 3, 'type': 'manager'},
                {'from_id': 5, 'to_id': 2, 'type': 'dotted_line'}
            ])
        """
        app_slug = self._ensure_app_slug(app_slug)
        path = f"/api/apps/{app_slug}/datatables/{table_name}/edges/"

        # Convert edges to API format (use 'from' and 'to' as aliases)
        formatted_edges = []
        for edge in edges:
            formatted_edge = {
                "from": edge.get("from_id") or edge.get("from"),
                "to": edge.get("to_id") or edge.get("to"),
                "type": edge.get("type", "default"),
            }
            if "metadata" in edge:
                formatted_edge["metadata"] = edge["metadata"]
            formatted_edges.append(formatted_edge)

        response = self._http.post(path, json=formatted_edges)
        return response

    def delete_edges(
        self,
        table_name: str,
        edge_ids: list[int],
        *,
        app_slug: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Delete multiple edges (relationships) by IDs.

        Args:
            table_name: Name of the table
            edge_ids: List of edge IDs to delete
            app_slug: Optional app slug override

        Returns:
            Dict with deletion result:
            {
                "deleted": 5,
                "message": "Successfully deleted 5 records"
            }

        Example:
            result = db.delete_edges('employees', edge_ids=[1, 2, 3])
        """
        app_slug = self._ensure_app_slug(app_slug)
        path = f"/api/apps/{app_slug}/datatables/{table_name}/edges/"

        payload = {"edge_ids": edge_ids}
        response = self._http.delete(path, json=payload)
        return response

    def get(
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
            record = db.get('users', 123)
        """
        app_slug = self._ensure_app_slug(app_slug)
        path = _DATATABLE_RECORD.format(
            app_slug=app_slug,
            table_name=table_name,
            record_id=str(record_id)
        )
        response = self._http.get(path)
        return self._extract_data(response)

    def create(
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
            record = db.create('users', {'name': 'John', 'age': 30})

            # Bulk records
            records = db.create('users', [
                {'name': 'Alice', 'age': 25},
                {'name': 'Bob', 'age': 35}
            ])
        """
        app_slug = self._ensure_app_slug(app_slug)
        path = _DATATABLE_DATA.format(app_slug=app_slug, table_name=table_name)
        response = self._http.post(path, json=data)
        return response.get("data")

    def update(
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
            record = db.update('users', 123, {'name': 'John Updated'})

            # Bulk record update
            records = db.update('users', [
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
            response = self._http.patch(path, json=record_id)
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
            response = self._http.patch(path, json=data)
            return self._extract_data(response)

    def delete(
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
            db.delete('users', 123)

            # Bulk delete by IDs
            result = db.delete('users', ids=[1, 2, 3])
            # Returns: {"deleted": 3, "message": "..."}

            # Bulk delete by filter
            result = db.delete('users', filter={'status': 'inactive'})
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
            self._http.delete(path)
            return None

        # Bulk delete by IDs or filter
        path = _DATATABLE_DATA.format(app_slug=app_slug, table_name=table_name)

        if ids is not None:
            # Delete by IDs - pass as query parameter
            ids_str = ','.join(str(id) for id in ids)
            response = self._http.delete(path, params={"ids": ids_str})
            return response

        if filter is not None:
            # Delete by filter - pass as JSON query parameter
            import json
            filter_json = json.dumps(filter)
            response = self._http.delete(path, params={"filter": filter_json})
            return response
