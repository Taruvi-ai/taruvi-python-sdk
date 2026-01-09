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

from taruvi.modules.base import BaseModule
from urllib.parse import urlencode
import json


if TYPE_CHECKING:
    from taruvi._async.client import AsyncClient

# API endpoint paths for storage
_STORAGE_BASE = "/api/apps/{app_slug}/storage/buckets/{bucket}/objects"
_STORAGE_OBJECT = "/api/apps/{app_slug}/storage/buckets/{bucket}/objects/{path}"
_STORAGE_BATCH_UPLOAD = "/api/apps/{app_slug}/storage/buckets/{bucket}/objects/batch-upload/"
_STORAGE_BATCH_DELETE = "/api/apps/{app_slug}/storage/buckets/{bucket}/objects/batch-delete/"

# API endpoint paths for bucket management
_STORAGE_BUCKETS = "/api/apps/{app_slug}/storage/buckets/"
_STORAGE_BUCKET = "/api/apps/{app_slug}/storage/buckets/{slug}/"

# API endpoint paths for object operations
_STORAGE_COPY = "/api/apps/{app_slug}/storage/buckets/{bucket}/objects/copy/"
_STORAGE_MOVE = "/api/apps/{app_slug}/storage/buckets/{bucket}/objects/move/"


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

class AsyncStorageQueryBuilder(_BaseStorageQueryBuilder):
    """Query builder for storage operations."""

    def __init__(
        self,
        client: "AsyncClient",
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
    ) -> "AsyncStorageQueryBuilder":
        """Add filters to the query."""
        self._add_filters(
            page, page_size, search, mimetype,
            mimetype_category, visibility, ordering, **kwargs
        )
        return self

    async def list(self) -> dict[str, Any]:
        """List files in the bucket with current filters."""
        path = _STORAGE_BASE.format(
            app_slug=self.app_slug,
            bucket=self.bucket
        )
        path += self.build_query_string()

        response = await self._http.get(path)
        return response

    async def upload(
        self,
        files: list[tuple[str, BinaryIO]],
        paths: list[str],
        metadatas: Optional[list[dict[str, Any]]] = None
    ) -> list[dict[str, Any]]:
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
        return files_data

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
    ) -> dict[str, Any]:
        """Update file metadata or visibility."""
        path = _STORAGE_OBJECT.format(
            app_slug=self.app_slug,
            bucket=self.bucket,
            path=file_path
        )

        body = _build_update_body(metadata, visibility)
        response = await self._http.put(path, json=body)
        return self._extract_data(response)

    async def delete(self, paths: list[str]) -> None:
        """Delete multiple files from the bucket."""
        path = _STORAGE_BATCH_DELETE.format(
            app_slug=self.app_slug,
            bucket=self.bucket
        )

        await self._http.post(path, json={"paths": paths})

    async def copy_object(
        self,
        source_path: str,
        destination_path: str,
        destination_bucket: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Copy an object to a new location.

        Args:
            source_path: Path to source object
            destination_path: Path for copied object
            destination_bucket: Target bucket slug (defaults to current bucket)

        Returns:
            Dict with new object metadata

        Examples:
            # Copy within same bucket
            new_obj = await storage.from_("my-bucket").copy_object(
                "users/123/avatar.jpg",
                "users/456/avatar.jpg"
            )

            # Copy to different bucket
            new_obj = await storage.from_("uploads").copy_object(
                "temp/file.pdf",
                "archive/file.pdf",
                destination_bucket="archives"
            )
        """
        path = _STORAGE_COPY.format(
            app_slug=self.app_slug,
            bucket=self.bucket
        )

        body: dict[str, Any] = {
            "source_path": source_path,
            "destination_path": destination_path
        }

        if destination_bucket:
            body["destination_bucket"] = destination_bucket

        response = await self._http.post(path, json=body)
        return self._extract_data(response)

    async def move_object(
        self,
        source_path: str,
        destination_path: str
    ) -> dict[str, Any]:
        """
        Move or rename an object within the bucket.

        WARNING: This copies the file to new location then deletes original.
        Large files may take several seconds.

        Args:
            source_path: Path to source object
            destination_path: New path for object

        Returns:
            Dict with updated object metadata

        Example:
            obj = await storage.from_("my-bucket").move_object(
                "temp/document.pdf",
                "archive/2024/document.pdf"
            )
        """
        path = _STORAGE_MOVE.format(
            app_slug=self.app_slug,
            bucket=self.bucket
        )

        body = {
            "source_path": source_path,
            "destination_path": destination_path
        }

        response = await self._http.post(path, json=body)
        return self._extract_data(response)


class AsyncStorageModule(BaseModule):
    """Storage API operations."""

    def __init__(self, client: "AsyncClient") -> None:
        """Initialize StorageModule."""
        self.client = client
        super().__init__(client._http_client, client._config)

    def from_(self, bucket: str, app_slug: Optional[str] = None) -> AsyncStorageQueryBuilder:
        """Select a bucket for storage operations."""
        return AsyncStorageQueryBuilder(self.client, bucket, app_slug)

    async def list_buckets(
        self,
        *,
        search: Optional[str] = None,
        visibility: Optional[str] = None,
        app_category: Optional[str] = None,
        ordering: Optional[str] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        app_slug: Optional[str] = None
    ) -> dict[str, Any]:
        """
        List all buckets in the app with optional filters.

        Args:
            search: Search by name or slug
            visibility: Filter by visibility ("public" or "private")
            app_category: Filter by category ("assets" or "attachments")
            ordering: Sort order (e.g., "-created_at", "name")
            page: Page number for pagination
            page_size: Items per page (max 100)
            app_slug: Override app_slug

        Returns:
            Dict with paginated bucket results:
            {
                "count": 42,
                "next": "...",
                "previous": "...",
                "results": [...]
            }

        Examples:
            # List all buckets
            response = await storage.list_buckets()
            buckets = response["results"]

            # Search and filter
            response = await storage.list_buckets(
                search="images",
                visibility="public",
                ordering="-created_at",
                page=1,
                page_size=20
            )
        """
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _STORAGE_BUCKETS.format(app_slug=app_slug)
        params: dict[str, Any] = {}

        if search:
            params["search"] = search
        if visibility:
            params["visibility"] = visibility
        if app_category:
            params["app_category"] = app_category
        if ordering:
            params["ordering"] = ordering
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["page_size"] = page_size

        response = await self._http.get(path, params=params)
        return self._extract_data(response)

    async def create_bucket(
        self,
        name: str,
        *,
        slug: Optional[str] = None,
        visibility: str = "private",
        file_size_limit: Optional[int] = None,
        allowed_mime_types: Optional[list[str]] = None,
        app_category: Optional[str] = None,
        app_slug: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Create a new storage bucket.

        Args:
            name: Bucket display name (required)
            slug: URL-friendly identifier (auto-generated if not provided)
            visibility: "public" or "private" (default: "private")
            file_size_limit: Max file size in bytes
            allowed_mime_types: List of allowed MIME types (e.g., ["image/*", "video/*"])
            app_category: "assets" or "attachments"
            app_slug: Override app_slug

        Returns:
            Dict with new bucket metadata

        Examples:
            # Simple bucket
            bucket = await storage.create_bucket("My Images")

            # With options
            bucket = await storage.create_bucket(
                "User Uploads",
                slug="user-uploads",
                visibility="private",
                file_size_limit=10485760,  # 10MB
                allowed_mime_types=["image/jpeg", "image/png"],
                app_category="assets"
            )
        """
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _STORAGE_BUCKETS.format(app_slug=app_slug)
        body: dict[str, Any] = {"name": name}

        if slug:
            body["slug"] = slug
        if visibility:
            body["visibility"] = visibility
        if file_size_limit is not None:
            body["file_size_limit"] = file_size_limit
        if allowed_mime_types:
            body["allowed_mime_types"] = allowed_mime_types
        if app_category:
            body["app_category"] = app_category

        response = await self._http.post(path, json=body)
        return self._extract_data(response)

    async def get_bucket(
        self,
        slug: str,
        *,
        app_slug: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Get a specific bucket by slug.

        Args:
            slug: Bucket slug identifier
            app_slug: Override app_slug

        Returns:
            Dict with bucket metadata

        Example:
            bucket = await storage.get_bucket("my-bucket")
        """
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _STORAGE_BUCKET.format(app_slug=app_slug, slug=slug)
        response = await self._http.get(path)
        return self._extract_data(response)

    async def update_bucket(
        self,
        slug: str,
        *,
        name: Optional[str] = None,
        visibility: Optional[str] = None,
        file_size_limit: Optional[int] = None,
        allowed_mime_types: Optional[list[str]] = None,
        app_category: Optional[str] = None,
        app_slug: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Update bucket settings.

        Args:
            slug: Bucket slug identifier
            name: New bucket name
            visibility: "public" or "private"
            file_size_limit: New max file size in bytes
            allowed_mime_types: New list of allowed MIME types
            app_category: "assets" or "attachments"
            app_slug: Override app_slug

        Returns:
            Dict with updated bucket metadata

        Example:
            bucket = await storage.update_bucket(
                "my-bucket",
                visibility="public",
                file_size_limit=104857600  # 100MB
            )
        """
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _STORAGE_BUCKET.format(app_slug=app_slug, slug=slug)
        body: dict[str, Any] = {}

        if name is not None:
            body["name"] = name
        if visibility is not None:
            body["visibility"] = visibility
        if file_size_limit is not None:
            body["file_size_limit"] = file_size_limit
        if allowed_mime_types is not None:
            body["allowed_mime_types"] = allowed_mime_types
        if app_category is not None:
            body["app_category"] = app_category

        response = await self._http.patch(path, json=body)
        return self._extract_data(response)

    async def delete_bucket(
        self,
        slug: str,
        *,
        app_slug: Optional[str] = None
    ) -> None:
        """
        Delete a bucket and all its objects.

        WARNING: This permanently deletes all files in the bucket.

        Args:
            slug: Bucket slug identifier
            app_slug: Override app_slug

        Example:
            await storage.delete_bucket("old-bucket")
        """
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _STORAGE_BUCKET.format(app_slug=app_slug, slug=slug)
        await self._http.delete(path)


