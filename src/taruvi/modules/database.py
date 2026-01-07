"""
Database API Module

Provides methods for:
- Querying data tables
- Filtering, sorting, pagination
- CRUD operations on records
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional


if TYPE_CHECKING:
    from taruvi.client import Client
    from taruvi.sync_client import SyncClient

# API endpoint paths for database
_DATATABLE_DATA = "/api/apps/{app_slug}/datatables/{table_name}/data/"
_DATATABLE_RECORD = "/api/apps/{app_slug}/datatables/{table_name}/data/{record_id}/"


# ============================================================================
# Shared Query Builder Logic
# ============================================================================

class _BaseQueryBuilder:
    """Base query builder with shared logic."""

    def __init__(self, table_name: str, app_slug: str) -> None:
        self.table_name = table_name
        self.app_slug = app_slug
        self._filters: dict[str, Any] = {}
        self._sort_field: Optional[str] = None
        self._sort_order: str = "asc"
        self._page_size: Optional[int] = None
        self._page: int = 1
        self._populate_fields: list[str] = []

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

    def build_params(self) -> dict[str, Any]:
        """Build query parameters for API request."""
        params: dict[str, Any] = {}
        params.update(self._filters)

        if self._sort_field:
            params["_sort"] = self._sort_field
            params["_order"] = self._sort_order

        if self._page_size is not None:
            params["page_size"] = self._page_size
        if self._page != 1:
            params["page"] = self._page

        if self._populate_fields:
            params["populate"] = ",".join(self._populate_fields)

        return params


# ============================================================================
# Async Implementation
# ============================================================================

class QueryBuilder(_BaseQueryBuilder):
    """Query builder for database operations."""

    def __init__(self, client: "Client", table_name: str, app_slug: Optional[str] = None) -> None:
        self.client = client
        self._http = client._http_client
        self._config = client._config
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")
        super().__init__(table_name, app_slug)

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

    async def get(self) -> list[dict[str, Any]]:
        """Execute query and get results."""
        path = _DATATABLE_DATA.format(
            app_slug=self.app_slug,
            table_name=self.table_name
        )
        params = self.build_params()

        response = await self._http.get(path, params=params)
        records = response.get("data", [])
        return records

    async def first(self) -> Optional[dict[str, Any]]:
        """Get first result."""
        results = await self.page_size(1).get()
        return results[0] if results else None

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


class DatabaseModule:
    """Database API operations."""

    def __init__(self, client: "Client") -> None:
        """Initialize Database module."""
        self.client = client
        self._http = client._http_client
        self._config = client._config

    def query(self, table_name: str, app_slug: Optional[str] = None) -> QueryBuilder:
        """Create a query builder for a table."""
        return QueryBuilder(self.client, table_name, app_slug)

    async def get(
        self,
        table_name: str,
        record_id: str | int,
        *,
        app_slug: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get a single record by ID.

        Args:
            table_name: Name of the table
            record_id: Record ID
            app_slug: Optional app slug override

        Returns:
            Single record as dict

        Example:
            record = await db.get('users', 123)
        """
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _DATATABLE_RECORD.format(
            app_slug=app_slug,
            table_name=table_name,
            record_id=str(record_id)
        )
        response = await self._http.get(path)
        return response.get("data", {})

    async def create(
        self,
        table_name: str,
        data: dict[str, Any] | list[dict[str, Any]],
        *,
        app_slug: Optional[str] = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """
        Create single or multiple records.

        Args:
            table_name: Name of the table
            data: Single record (dict) or multiple records (list of dicts)
            app_slug: Optional app slug override

        Returns:
            Single record (dict) if input was dict
            List of records if input was list

        Examples:
            # Single record
            record = await db.create('users', {'name': 'John', 'age': 30})

            # Bulk records
            records = await db.create('users', [
                {'name': 'Alice', 'age': 25},
                {'name': 'Bob', 'age': 35}
            ])
        """
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _DATATABLE_DATA.format(app_slug=app_slug, table_name=table_name)
        response = await self._http.post(path, json=data)

        # Backend auto-detects single vs bulk
        # Single: {"data": {...}}
        # Bulk: {"data": [...], "count": N}
        return response.get("data")

    async def update(
        self,
        table_name: str,
        record_id: str | int | list[dict[str, Any]],
        data: Optional[dict[str, Any]] = None,
        *,
        app_slug: Optional[str] = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
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
            Single record (dict) if single update
            List of records if bulk update

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
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        # Detect single vs bulk update
        if isinstance(record_id, list):
            # Bulk update
            if data is not None:
                raise ValueError("data parameter not allowed for bulk update")

            path = _DATATABLE_DATA.format(app_slug=app_slug, table_name=table_name)
            response = await self._http.patch(path, json=record_id)
            return response.get("data", [])
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
            return response.get("data", {})

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
            # Returns: {"deleted_count": 3, "message": "..."}

            # Bulk delete by filter
            result = await db.delete('users', filter={'status': 'inactive'})
            # Returns: {"deleted_count": 42, "message": "..."}
        """
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

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


# ============================================================================
# Sync Implementation
# ============================================================================

class SyncQueryBuilder(_BaseQueryBuilder):
    """Synchronous query builder for database operations."""

    def __init__(self, client: "SyncClient", table_name: str, app_slug: Optional[str] = None) -> None:
        self.client = client
        self._http = client._http
        self._config = client._config
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")
        super().__init__(table_name, app_slug)

    def filter(self, field: str, operator: str, value: Any) -> "SyncQueryBuilder":
        """Add a filter to the query."""
        self._add_filter(field, operator, value)
        return self

    def sort(self, field: str, order: str = "asc") -> "SyncQueryBuilder":
        """Add sorting to the query."""
        self._set_sort(field, order)
        return self

    def page_size(self, page_size: int) -> "SyncQueryBuilder":
        """Set number of records per page."""
        self._set_page_size(page_size)
        return self

    def page(self, page: int) -> "SyncQueryBuilder":
        """Set page number (1-indexed)."""
        self._set_page(page)
        return self

    def populate(self, *fields: str) -> "SyncQueryBuilder":
        """Populate related fields (foreign keys)."""
        self._add_populate(*fields)
        return self

    def get(self) -> list[dict[str, Any]]:
        """Execute query and get results (blocking)."""
        path = _DATATABLE_DATA.format(
            app_slug=self.app_slug,
            table_name=self.table_name
        )
        params = self.build_params()

        response = self._http.get(path, params=params)
        records = response.get("data", [])
        return records

    def first(self) -> Optional[dict[str, Any]]:
        """Get first result (blocking)."""
        results = self.page_size(1).get()
        return results[0] if results else None

    def count(self) -> int:
        """Get count of matching records (blocking)."""
        path = _DATATABLE_DATA.format(
            app_slug=self.app_slug,
            table_name=self.table_name
        )
        params = self.build_params()
        params["_count"] = "true"

        response = self._http.get(path, params=params)
        return response.get("total", 0)


class SyncDatabaseModule:
    """Synchronous Database API operations."""

    def __init__(self, client: "SyncClient") -> None:
        """Initialize synchronous Database module."""
        self.client = client
        self._http = client._http
        self._config = client._config

    def query(self, table_name: str, app_slug: Optional[str] = None) -> SyncQueryBuilder:
        """Create a query builder for a table."""
        return SyncQueryBuilder(self.client, table_name, app_slug)

    def get(
        self,
        table_name: str,
        record_id: str | int,
        *,
        app_slug: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get a single record by ID (blocking).

        Args:
            table_name: Name of the table
            record_id: Record ID
            app_slug: Optional app slug override

        Returns:
            Single record as dict

        Example:
            record = db.get('users', 123)
        """
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _DATATABLE_RECORD.format(
            app_slug=app_slug,
            table_name=table_name,
            record_id=str(record_id)
        )
        response = self._http.get(path)
        return response.get("data", {})

    def create(
        self,
        table_name: str,
        data: dict[str, Any] | list[dict[str, Any]],
        *,
        app_slug: Optional[str] = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """
        Create single or multiple records (blocking).

        Args:
            table_name: Name of the table
            data: Single record (dict) or multiple records (list of dicts)
            app_slug: Optional app slug override

        Returns:
            Single record (dict) if input was dict
            List of records if input was list

        Examples:
            # Single record
            record = db.create('users', {'name': 'John', 'age': 30})

            # Bulk records
            records = db.create('users', [
                {'name': 'Alice', 'age': 25},
                {'name': 'Bob', 'age': 35}
            ])
        """
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _DATATABLE_DATA.format(app_slug=app_slug, table_name=table_name)
        response = self._http.post(path, json=data)

        # Backend auto-detects single vs bulk
        # Single: {"data": {...}}
        # Bulk: {"data": [...], "count": N}
        return response.get("data")

    def update(
        self,
        table_name: str,
        record_id: str | int | list[dict[str, Any]],
        data: Optional[dict[str, Any]] = None,
        *,
        app_slug: Optional[str] = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """
        Update single record by ID or multiple records in bulk (blocking).

        Args:
            table_name: Name of the table
            record_id:
                - For single update: Record ID (int/str)
                - For bulk update: List of dicts with 'id' field
            data: Update data (only for single record update)
            app_slug: Optional app slug override

        Returns:
            Single record (dict) if single update
            List of records if bulk update

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
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        # Detect single vs bulk update
        if isinstance(record_id, list):
            # Bulk update
            if data is not None:
                raise ValueError("data parameter not allowed for bulk update")

            path = _DATATABLE_DATA.format(app_slug=app_slug, table_name=table_name)
            response = self._http.patch(path, json=record_id)
            return response.get("data", [])
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
            return response.get("data", {})

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
        Delete single record by ID, multiple records by IDs, or records matching filter (blocking).

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
            # Returns: {"deleted_count": 3, "message": "..."}

            # Bulk delete by filter
            result = db.delete('users', filter={'status': 'inactive'})
            # Returns: {"deleted_count": 42, "message": "..."}
        """
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

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
