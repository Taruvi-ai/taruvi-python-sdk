"""
Synchronous Database API Module

Native blocking implementation (no asyncio wrappers).
Provides methods for:
- Querying data tables
- Filtering, sorting, pagination
- CRUD operations on records
"""

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from taruvi.sync_client import SyncClient


class SyncQueryBuilder:
    """
    Synchronous query builder for database operations (native blocking).

    Provides a fluent interface for building queries with filters, sorting, and pagination.
    """

    def __init__(self, client: "SyncClient", table_name: str, app_slug: Optional[str] = None) -> None:
        """
        Initialize synchronous query builder.

        Args:
            client: SyncClient instance
            table_name: Table name to query
            app_slug: App slug (defaults to client's app_slug)
        """
        self.client = client
        self._http = client._http
        self._config = client._config
        self.table_name = table_name
        self.app_slug = app_slug or self._config.app_slug

        if not self.app_slug:
            raise ValueError("app_slug is required")

        # Query parameters
        self._filters: dict[str, Any] = {}
        self._sort_field: Optional[str] = None
        self._sort_order: str = "asc"
        self._limit_value: Optional[int] = None
        self._offset_value: int = 0
        self._populate_fields: list[str] = []

    def filter(self, field: str, operator: str, value: Any) -> "SyncQueryBuilder":
        """
        Add a filter to the query.

        Args:
            field: Field name to filter on
            operator: Filter operator (eq, gt, gte, lt, lte, in, contains, etc.)
            value: Value to filter by

        Returns:
            SyncQueryBuilder: Self for chaining

        Example:
            ```python
            query.filter("status", "eq", "active")
            query.filter("age", "gte", 18)
            query.filter("tags", "contains", "python")
            ```
        """
        if operator == "eq":
            self._filters[field] = value
        else:
            self._filters[f"{field}__{operator}"] = value
        return self

    def sort(self, field: str, order: str = "asc") -> "SyncQueryBuilder":
        """
        Add sorting to the query.

        Args:
            field: Field name to sort by
            order: Sort order ("asc" or "desc")

        Returns:
            SyncQueryBuilder: Self for chaining

        Example:
            ```python
            query.sort("created_at", "desc")
            ```
        """
        self._sort_field = field
        self._sort_order = order
        return self

    def limit(self, limit: int) -> "SyncQueryBuilder":
        """
        Limit number of results.

        Args:
            limit: Maximum number of records to return

        Returns:
            SyncQueryBuilder: Self for chaining

        Example:
            ```python
            query.limit(10)
            ```
        """
        self._limit_value = limit
        return self

    def offset(self, offset: int) -> "SyncQueryBuilder":
        """
        Set offset for pagination.

        Args:
            offset: Number of records to skip

        Returns:
            SyncQueryBuilder: Self for chaining

        Example:
            ```python
            query.offset(20)
            ```
        """
        self._offset_value = offset
        return self

    def populate(self, *fields: str) -> "SyncQueryBuilder":
        """
        Populate related fields (foreign keys).

        Args:
            *fields: Field names to populate

        Returns:
            SyncQueryBuilder: Self for chaining

        Example:
            ```python
            query.populate("author", "comments")
            ```
        """
        self._populate_fields.extend(fields)
        return self

    def _build_params(self) -> dict[str, Any]:
        """Build query parameters for API request."""
        params: dict[str, Any] = {}

        # Add filters
        params.update(self._filters)

        # Add sorting
        if self._sort_field:
            params["_sort"] = self._sort_field
            params["_order"] = self._sort_order

        # Add pagination
        if self._limit_value is not None:
            params["limit"] = self._limit_value
        if self._offset_value:
            params["offset"] = self._offset_value

        # Add population
        if self._populate_fields:
            params["populate"] = ",".join(self._populate_fields)

        return params

    def get(self) -> list[dict[str, Any]]:
        """
        Execute query and get results (blocking).

        Returns:
            list[dict]: List of records

        Example:
            ```python
            users = client.database.query("users") \\
                .filter("is_active", "eq", True) \\
                .sort("created_at", "desc") \\
                .limit(10) \\
                .get()
            ```
        """
        path = f"/api/apps/{self.app_slug}/datatables/{self.table_name}/data/"
        params = self._build_params()

        response = self._http.get(path, params=params)
        return response.get("data", [])

    def first(self) -> Optional[dict[str, Any]]:
        """
        Get first result (blocking).

        Returns:
            Optional[dict]: First record or None

        Example:
            ```python
            user = client.database.query("users") \\
                .filter("email", "eq", "alice@example.com") \\
                .first()
            ```
        """
        results = self.limit(1).get()
        return results[0] if results else None

    def count(self) -> int:
        """
        Get count of matching records (blocking).

        Returns:
            int: Number of matching records

        Example:
            ```python
            count = client.database.query("users") \\
                .filter("is_active", "eq", True) \\
                .count()
            ```
        """
        path = f"/api/apps/{self.app_slug}/datatables/{self.table_name}/data/"
        params = self._build_params()
        params["_count"] = "true"

        response = self._http.get(path, params=params)
        return response.get("total", 0)


class SyncDatabaseModule:
    """Synchronous Database API operations (native blocking)."""

    def __init__(self, client: "SyncClient") -> None:
        """
        Initialize synchronous Database module.

        Args:
            client: SyncClient instance
        """
        self.client = client
        self._http = client._http
        self._config = client._config

    def query(self, table_name: str, app_slug: Optional[str] = None) -> SyncQueryBuilder:
        """
        Create a query builder for a table.

        Args:
            table_name: Table name to query
            app_slug: App slug (defaults to client's app_slug)

        Returns:
            SyncQueryBuilder: Query builder instance

        Example:
            ```python
            # Build and execute query
            users = client.database.query("users") \\
                .filter("status", "eq", "active") \\
                .sort("created_at", "desc") \\
                .limit(10) \\
                .get()

            # Get single record
            user = client.database.query("users") \\
                .filter("email", "eq", "alice@example.com") \\
                .first()

            # Count records
            count = client.database.query("users") \\
                .filter("is_active", "eq", True) \\
                .count()
            ```
        """
        return SyncQueryBuilder(self.client, table_name, app_slug)

    def create(
        self,
        table_name: str,
        data: dict[str, Any],
        *,
        app_slug: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Create a new record (blocking).

        Args:
            table_name: Table name
            data: Record data
            app_slug: App slug (defaults to client's app_slug)

        Returns:
            dict: Created record

        Example:
            ```python
            user = client.database.create("users", {
                "name": "Alice",
                "email": "alice@example.com",
                "is_active": True
            })
            ```
        """
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = f"/api/apps/{app_slug}/datatables/{table_name}/data/"
        response = self._http.post(path, json=data)
        return response.get("data", {})

    def update(
        self,
        table_name: str,
        record_id: str | int,
        data: dict[str, Any],
        *,
        app_slug: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Update a record (blocking).

        Args:
            table_name: Table name
            record_id: Record ID
            data: Updated data
            app_slug: App slug (defaults to client's app_slug)

        Returns:
            dict: Updated record

        Example:
            ```python
            user = client.database.update("users", 123, {
                "is_active": False
            })
            ```
        """
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = f"/api/apps/{app_slug}/datatables/{table_name}/data/{record_id}/"
        response = self._http.put(path, json=data)
        return response.get("data", {})

    def delete(
        self,
        table_name: str,
        record_id: str | int,
        *,
        app_slug: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Delete a record (blocking).

        Args:
            table_name: Table name
            record_id: Record ID
            app_slug: App slug (defaults to client's app_slug)

        Returns:
            dict: Deletion confirmation

        Example:
            ```python
            client.database.delete("users", 123)
            ```
        """
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = f"/api/apps/{app_slug}/datatables/{table_name}/data/{record_id}/"
        response = self._http.delete(path)
        return response
