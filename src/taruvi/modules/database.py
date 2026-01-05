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
        self._limit_value: Optional[int] = None
        self._offset_value: int = 0
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

    def _set_limit(self, limit: int) -> None:
        """Set limit (shared logic)."""
        self._limit_value = limit

    def _set_offset(self, offset: int) -> None:
        """Set offset (shared logic)."""
        self._offset_value = offset

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

        if self._limit_value is not None:
            params["limit"] = self._limit_value
        if self._offset_value:
            params["offset"] = self._offset_value

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

    def limit(self, limit: int) -> "QueryBuilder":
        """Limit number of results."""
        self._set_limit(limit)
        return self

    def offset(self, offset: int) -> "QueryBuilder":
        """Set offset for pagination."""
        self._set_offset(offset)
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
        results = await self.limit(1).get()
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

    async def create(
        self,
        table_name: str,
        data: dict[str, Any],
        *,
        app_slug: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create a new record."""
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _DATATABLE_DATA.format(app_slug=app_slug, table_name=table_name)
        response = await self._http.post(path, json=data)
        record = response.get("data", {})
        return record

    async def update(
        self,
        table_name: str,
        record_id: str | int,
        data: dict[str, Any],
        *,
        app_slug: Optional[str] = None,
    ) -> dict[str, Any]:
        """Update a record."""
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _DATATABLE_RECORD.format(
            app_slug=app_slug,
            table_name=table_name,
            record_id=str(record_id)
        )
        response = await self._http.put(path, json=data)
        record = response.get("data", {})
        return record

    async def delete(
        self,
        table_name: str,
        record_id: str | int,
        *,
        app_slug: Optional[str] = None,
    ) -> None:
        """Delete a record."""
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _DATATABLE_RECORD.format(
            app_slug=app_slug,
            table_name=table_name,
            record_id=str(record_id)
        )
        await self._http.delete(path)


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

    def limit(self, limit: int) -> "SyncQueryBuilder":
        """Limit number of results."""
        self._set_limit(limit)
        return self

    def offset(self, offset: int) -> "SyncQueryBuilder":
        """Set offset for pagination."""
        self._set_offset(offset)
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
        results = self.limit(1).get()
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

    def create(
        self,
        table_name: str,
        data: dict[str, Any],
        *,
        app_slug: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create a new record (blocking)."""
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _DATATABLE_DATA.format(app_slug=app_slug, table_name=table_name)
        response = self._http.post(path, json=data)
        record = response.get("data", {})
        return record

    def update(
        self,
        table_name: str,
        record_id: str | int,
        data: dict[str, Any],
        *,
        app_slug: Optional[str] = None,
    ) -> dict[str, Any]:
        """Update a record (blocking)."""
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _DATATABLE_RECORD.format(
            app_slug=app_slug,
            table_name=table_name,
            record_id=str(record_id)
        )
        response = self._http.put(path, json=data)
        record = response.get("data", {})
        return record

    def delete(
        self,
        table_name: str,
        record_id: str | int,
        *,
        app_slug: Optional[str] = None,
    ) -> None:
        """Delete a record (blocking)."""
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _DATATABLE_RECORD.format(
            app_slug=app_slug,
            table_name=table_name,
            record_id=str(record_id)
        )
        self._http.delete(path)
