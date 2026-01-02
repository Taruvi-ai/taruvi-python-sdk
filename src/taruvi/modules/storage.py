"""
Storage API Module

Provides methods for:
- File upload/download
- File management (update metadata, delete)
- Bucket operations with query builder
- File filtering and pagination
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, BinaryIO
from urllib.parse import urlencode
import json

from taruvi.models.storage import StorageObject, StorageListResponse

if TYPE_CHECKING:
    from taruvi.client import Client
    from taruvi.sync_client import SyncClient

# API endpoint paths for storage
_STORAGE_BASE = "/api/apps/{app_slug}/storage/buckets/{bucket}/objects"
_STORAGE_OBJECT = "/api/apps/{app_slug}/storage/buckets/{bucket}/objects/{path}"
_STORAGE_BATCH_UPLOAD = "/api/apps/{app_slug}/storage/buckets/{bucket}/objects/batch-upload/"
_STORAGE_BATCH_DELETE = "/api/apps/{app_slug}/storage/buckets/{bucket}/objects/batch-delete/"


# ============================================================================
# Shared Query Builder Logic
# ============================================================================

class _BaseStorageQueryBuilder:
    """Base storage query builder with shared logic."""
    
    def __init__(self, bucket: str, app_slug: str) -> None:
        self.bucket = bucket
        self.app_slug = app_slug
        self._filters: dict[str, Any] = {}

    def _add_filters(
        self,
        page: Optional[int],
        page_size: Optional[int],
        search: Optional[str],
        mimetype: Optional[str],
        mimetype_category: Optional[str],
        visibility: Optional[str],
        ordering: Optional[str],
        **kwargs: Any
    ) -> None:
        """Add filters to the query (shared logic)."""
        if page is not None:
            self._filters["page"] = page
        if page_size is not None:
            self._filters["page_size"] = page_size
        if search:
            self._filters["search"] = search
        if mimetype:
            self._filters["mimetype"] = mimetype
        if mimetype_category:
            self._filters["mimetype_category"] = mimetype_category
        if visibility:
            self._filters["visibility"] = visibility
        if ordering:
            self._filters["ordering"] = ordering

        # Add any additional filter kwargs
        self._filters.update(kwargs)

    def build_query_string(self) -> str:
        """Build query string from filters."""
        if not self._filters:
            return ""
        return "?" + urlencode(self._filters)


def _build_update_body(
    metadata: Optional[dict[str, Any]],
    visibility: Optional[str]
) -> dict[str, Any]:
    """Build update request body."""
    body: dict[str, Any] = {}
    if metadata is not None:
        body["metadata"] = metadata
    if visibility is not None:
        body["visibility"] = visibility
    return body


# ============================================================================
# Async Implementation
# ============================================================================

class StorageQueryBuilder(_BaseStorageQueryBuilder):
    """Query builder for storage operations."""

    def __init__(
        self,
        client: "Client",
        bucket: str,
        app_slug: Optional[str] = None
    ) -> None:
        self.client = client
        self._http = client._http_client
        self._config = client._config
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")
        super().__init__(bucket, app_slug)

    def filter(
        self,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        search: Optional[str] = None,
        mimetype: Optional[str] = None,
        mimetype_category: Optional[str] = None,
        visibility: Optional[str] = None,
        ordering: Optional[str] = None,
        **kwargs: Any
    ) -> "StorageQueryBuilder":
        """Add filters to the query."""
        self._add_filters(
            page, page_size, search, mimetype,
            mimetype_category, visibility, ordering, **kwargs
        )
        return self

    async def list(self) -> StorageListResponse:
        """List files in the bucket with current filters."""
        path = _STORAGE_BASE.format(
            app_slug=self.app_slug,
            bucket=self.bucket
        )
        path += self.build_query_string()

        response = await self._http.get(path)
        return StorageListResponse.from_dict(response)

    async def upload(
        self,
        files: list[tuple[str, BinaryIO]],
        paths: list[str],
        metadatas: Optional[list[dict[str, Any]]] = None
    ) -> list[StorageObject]:
        """Upload multiple files to the bucket."""
        import aiohttp

        path = _STORAGE_BATCH_UPLOAD.format(
            app_slug=self.app_slug,
            bucket=self.bucket
        )

        # Create FormData
        form = aiohttp.FormData()

        # Add files
        for filename, file_obj in files:
            form.add_field(
                "files",
                file_obj,
                filename=filename,
                content_type="application/octet-stream"
            )

        # Add paths as JSON string
        form.add_field("paths", json.dumps(paths))

        # Add metadata as JSON string
        if metadatas:
            form.add_field("metadata", json.dumps(metadatas))

        # Use custom headers for FormData
        headers = self._config.headers.copy()
        headers.pop("Content-Type", None)

        response = await self._http.client.post(
            f"{self._config.api_url}{path}",
            data=form,
            headers=headers
        )

        data = response.json()
        files_data = data.get("data", [])
        return [StorageObject.from_dict(f) for f in files_data]

    async def download(self, file_path: str) -> bytes:
        """Download a file from the bucket."""
        path = _STORAGE_OBJECT.format(
            app_slug=self.app_slug,
            bucket=self.bucket,
            path=file_path
        )

        response = await self._http.client.get(
            f"{self._config.api_url}{path}",
            headers=self._config.headers
        )
        return response.content

    async def update(
        self,
        file_path: str,
        metadata: Optional[dict[str, Any]] = None,
        visibility: Optional[str] = None
    ) -> StorageObject:
        """Update file metadata or visibility."""
        path = _STORAGE_OBJECT.format(
            app_slug=self.app_slug,
            bucket=self.bucket,
            path=file_path
        )

        body = _build_update_body(metadata, visibility)
        response = await self._http.put(path, json=body)
        return StorageObject.from_dict(response.get("data", {}))

    async def delete(self, paths: list[str]) -> None:
        """Delete multiple files from the bucket."""
        path = _STORAGE_BATCH_DELETE.format(
            app_slug=self.app_slug,
            bucket=self.bucket
        )

        await self._http.post(path, json={"paths": paths})


class StorageModule:
    """Storage API operations."""

    def __init__(self, client: "Client") -> None:
        """Initialize Storage module."""
        self.client = client
        self._http = client._http_client
        self._config = client._config

    def from_(self, bucket: str, app_slug: Optional[str] = None) -> StorageQueryBuilder:
        """Select a bucket for storage operations."""
        return StorageQueryBuilder(self.client, bucket, app_slug)


# ============================================================================
# Sync Implementation
# ============================================================================

class SyncStorageQueryBuilder(_BaseStorageQueryBuilder):
    """Synchronous query builder for storage operations."""

    def __init__(
        self,
        client: "SyncClient",
        bucket: str,
        app_slug: Optional[str] = None
    ) -> None:
        self.client = client
        self._http = client._http
        self._config = client._config
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")
        super().__init__(bucket, app_slug)

    def filter(
        self,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        search: Optional[str] = None,
        mimetype: Optional[str] = None,
        mimetype_category: Optional[str] = None,
        visibility: Optional[str] = None,
        ordering: Optional[str] = None,
        **kwargs: Any
    ) -> "SyncStorageQueryBuilder":
        """Add filters to the query."""
        self._add_filters(
            page, page_size, search, mimetype,
            mimetype_category, visibility, ordering, **kwargs
        )
        return self

    def list(self) -> StorageListResponse:
        """List files in the bucket with current filters (blocking)."""
        path = _STORAGE_BASE.format(
            app_slug=self.app_slug,
            bucket=self.bucket
        )
        path += self.build_query_string()

        response = self._http.get(path)
        return StorageListResponse.from_dict(response)

    def upload(
        self,
        files: list[tuple[str, BinaryIO]],
        paths: list[str],
        metadatas: Optional[list[dict[str, Any]]] = None
    ) -> list[StorageObject]:
        """Upload multiple files to the bucket (blocking)."""
        path = _STORAGE_BATCH_UPLOAD.format(
            app_slug=self.app_slug,
            bucket=self.bucket
        )

        # Create multipart form data for httpx
        files_data = [
            ("files", (filename, file_obj, "application/octet-stream"))
            for filename, file_obj in files
        ]

        data = {
            "paths": json.dumps(paths),
        }

        if metadatas:
            data["metadata"] = json.dumps(metadatas)

        # Use httpx's multipart form data
        response = self._http.client.post(
            f"{self._config.api_url}{path}",
            files=files_data,
            data=data,
            headers={k: v for k, v in self._config.headers.items() if k != "Content-Type"}
        )

        response_data = response.json()
        files_list = response_data.get("data", [])
        return [StorageObject.from_dict(f) for f in files_list]

    def download(self, file_path: str) -> bytes:
        """Download a file from the bucket (blocking)."""
        path = _STORAGE_OBJECT.format(
            app_slug=self.app_slug,
            bucket=self.bucket,
            path=file_path
        )

        response = self._http.client.get(
            f"{self._config.api_url}{path}",
            headers=self._config.headers
        )
        return response.content

    def update(
        self,
        file_path: str,
        metadata: Optional[dict[str, Any]] = None,
        visibility: Optional[str] = None
    ) -> StorageObject:
        """Update file metadata or visibility (blocking)."""
        path = _STORAGE_OBJECT.format(
            app_slug=self.app_slug,
            bucket=self.bucket,
            path=file_path
        )

        body = _build_update_body(metadata, visibility)
        response = self._http.put(path, json=body)
        return StorageObject.from_dict(response.get("data", {}))

    def delete(self, paths: list[str]) -> None:
        """Delete multiple files from the bucket (blocking)."""
        path = _STORAGE_BATCH_DELETE.format(
            app_slug=self.app_slug,
            bucket=self.bucket
        )

        self._http.post(path, json={"paths": paths})


class SyncStorageModule:
    """Synchronous Storage API operations."""

    def __init__(self, client: "SyncClient") -> None:
        """Initialize Storage module."""
        self.client = client
        self._http = client._http
        self._config = client._config

    def from_(self, bucket: str, app_slug: Optional[str] = None) -> SyncStorageQueryBuilder:
        """Select a bucket for storage operations (blocking)."""
        return SyncStorageQueryBuilder(self.client, bucket, app_slug)
