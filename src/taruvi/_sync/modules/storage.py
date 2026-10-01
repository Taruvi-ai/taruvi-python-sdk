"""
Storage API Module

Provides methods for:
- File upload/download
- File management (update metadata, delete)
- Bucket operations with query builder
- File filtering and pagination
"""

from __future__ import annotations

import json
import mimetypes
from typing import TYPE_CHECKING, Any, BinaryIO, Literal, Optional
from urllib.parse import quote

import httpx

from taruvi.http_client_base import transport_error
from taruvi.modules.base import BaseModule
from taruvi.types import Bucket, StorageAccessLinkResult, StorageBrowseData, StorageFile
from taruvi.utils import build_params, build_query_string

if TYPE_CHECKING:
    from taruvi._sync.client import SyncClient

# API endpoint paths for storage
_STORAGE_BASE = "/api/apps/{app_slug}/storage/buckets/{bucket}/objects/"
_STORAGE_OBJECT = "/api/apps/{app_slug}/storage/buckets/{bucket}/objects/{path}/"
_STORAGE_BATCH_UPLOAD = "/api/apps/{app_slug}/storage/buckets/{bucket}/objects/batch-upload/"
_STORAGE_BATCH_DELETE = "/api/apps/{app_slug}/storage/buckets/{bucket}/objects/batch-delete/"

# API endpoint paths for bucket management
_STORAGE_BUCKETS = "/api/apps/{app_slug}/storage/buckets/"
_STORAGE_BUCKET = "/api/apps/{app_slug}/storage/buckets/{slug}/"

# API endpoint paths for object operations
_STORAGE_COPY = "/api/apps/{app_slug}/storage/buckets/{bucket}/objects/copy/"
_STORAGE_MOVE = "/api/apps/{app_slug}/storage/buckets/{bucket}/objects/move/"
_STORAGE_VIEW = "/api/apps/{app_slug}/storage/buckets/{bucket}/objects/{path}/view/"
_STORAGE_EDIT = "/api/apps/{app_slug}/storage/buckets/{bucket}/objects/{path}/edit/"
_STORAGE_BROWSE = "/api/apps/{app_slug}/storage/buckets/{bucket}/objects/browse/"


# ============================================================================
# Shared Query Builder Logic
# ============================================================================


def _encode_object_path(file_path: str) -> str:
    """URL-encode each segment of an object path, keeping the slashes."""
    return "/".join(quote(segment, safe="") for segment in file_path.split("/"))


def _guess_content_type(filename: str) -> str:
    """Guess a file's content type from its name."""
    return mimetypes.guess_type(filename)[0] or "application/octet-stream"


class _BaseStorageQueryBuilder:
    """Base storage query builder with shared logic."""

    def __init__(self, bucket: str, app_slug: str) -> None:
        self.bucket = bucket
        self.app_slug = app_slug
        self._filters: dict[str, Any] = {}

    def _extract_data(self, response: dict[str, Any]) -> Any:
        """Extract 'data' field from API response."""
        return response.get("data", {})

    def _add_filters(
        self,
        page: Optional[int],
        page_size: Optional[int],
        search: Optional[str],
        mimetype: Optional[str],
        mimetype_category: Optional[str],
        visibility: Optional[str],
        ordering: Optional[str],
        **kwargs: Any,
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
        return build_query_string(self._filters)


def _build_update_body(
    metadata: Optional[dict[str, Any]], visibility: Optional[str]
) -> dict[str, Any]:
    """Build update request body."""
    body: dict[str, Any] = {}
    if metadata is not None:
        body["metadata"] = metadata
    if visibility is not None:
        body["visibility"] = visibility
    return body


# ============================================================================
# Sync Implementation
# ============================================================================


class StorageQueryBuilder(_BaseStorageQueryBuilder):
    """Query builder for storage operations."""

    def __init__(self, client: SyncClient, bucket: str, app_slug: Optional[str] = None) -> None:
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
        **kwargs: Any,
    ) -> StorageQueryBuilder:
        """Add filters to the query."""
        self._add_filters(
            page, page_size, search, mimetype, mimetype_category, visibility, ordering, **kwargs
        )
        return self

    def list(self) -> dict[str, Any]:
        """List files in the bucket with current filters."""
        path = _STORAGE_BASE.format(app_slug=self.app_slug, bucket=self.bucket)
        path += self.build_query_string()

        response = self._http.get(path)
        return response

    def upload(
        self,
        files: list[tuple[str, BinaryIO]] | list[tuple[str, BinaryIO, str]],
        paths: list[str],
        metadatas: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        """Upload multiple files to the bucket.

        Each entry of ``files`` is ``(filename, file_obj)`` or
        ``(filename, file_obj, content_type)``. Without a content type, it is
        guessed from the filename.

        Returns:
            The batch result: ``uploaded_count``, ``failed_count``, ``total``,
            and the ``successful`` and ``failed`` entries.
        """
        path = _STORAGE_BATCH_UPLOAD.format(app_slug=self.app_slug, bucket=self.bucket)

        # Prepare multipart files for httpx
        # Format: [('field_name', ('filename', file_obj, 'content_type'))]
        httpx_files = [
            (
                "files",
                (entry[0], entry[1], entry[2] if len(entry) > 2 else _guess_content_type(entry[0])),
            )
            for entry in files
        ]

        # Prepare form data (paths and metadata as JSON strings)
        data = {"paths": json.dumps(paths)}
        if metadatas:
            data["metadata"] = json.dumps(metadatas)

        # Exclude Content-Type so httpx auto-sets multipart/form-data with boundary
        headers = {k: v for k, v in self._config.headers.items() if k != "Content-Type"}
        try:
            response = self._http.client.post(
                f"{self._config.api_url}{path}", files=httpx_files, data=data, headers=headers
            )
        except httpx.TransportError as error:
            raise transport_error(
                error,
                method="POST",
                path=path,
                api_url=self._config.api_url,
                timeout=self._config.timeout,
            ) from error
        response_data = self._http._handle_response(response)
        return response_data.get("data", {})

    def download(self, file_path: str) -> bytes:
        """Download a file from the bucket."""
        path = _STORAGE_OBJECT.format(
            app_slug=self.app_slug, bucket=self.bucket, path=_encode_object_path(file_path)
        )

        try:
            response = self._http.client.get(
                f"{self._config.api_url}{path}", headers=self._config.headers
            )
        except httpx.TransportError as error:
            raise transport_error(
                error,
                method="GET",
                path=path,
                api_url=self._config.api_url,
                timeout=self._config.timeout,
            ) from error
        if response.status_code >= 400:
            self._http._handle_error_response(response)
        return response.content

    def update(
        self,
        file_path: str,
        metadata: Optional[dict[str, Any]] = None,
        visibility: Optional[str] = None,
    ) -> StorageFile:
        """Update file metadata or visibility."""
        path = _STORAGE_OBJECT.format(
            app_slug=self.app_slug, bucket=self.bucket, path=_encode_object_path(file_path)
        )

        body = _build_update_body(metadata, visibility)
        response = self._http.patch(path, json=body)
        return self._extract_data(response)

    def delete(self, paths: list[str]) -> dict[str, Any]:
        """Delete multiple files from the bucket.

        Returns:
            The batch result: ``deleted_count`` and ``failed``. Objects the
            platform skips, because they're missing or a policy denies the
            delete, are listed in ``failed`` rather than raising.
        """
        path = _STORAGE_BATCH_DELETE.format(app_slug=self.app_slug, bucket=self.bucket)

        response = self._http.post(path, json={"paths": paths})
        return response.get("data", {})

    def view_access(self, file_path: str) -> StorageAccessLinkResult:
        """Get a SharePoint view-access URL for an Office file."""
        path = _STORAGE_VIEW.format(
            app_slug=self.app_slug, bucket=self.bucket, path=_encode_object_path(file_path)
        )
        response = self._http.get(path)
        return self._extract_data(response)

    def edit_access(self, file_path: str) -> StorageAccessLinkResult:
        """Get a SharePoint edit-access URL for an Office file."""
        path = _STORAGE_EDIT.format(
            app_slug=self.app_slug, bucket=self.bucket, path=_encode_object_path(file_path)
        )
        response = self._http.get(path)
        return self._extract_data(response)

    def browse(
        self,
        *,
        prefix: str = "",
        page: int = 1,
        page_size: int = 50,
        sort: Optional[Literal["name", "size", "created_at", "updated_at"]] = None,
        order: Optional[Literal["asc", "desc"]] = None,
    ) -> StorageBrowseData:
        """Browse bucket as a folder view — returns virtual folders and files at a prefix."""
        path = _STORAGE_BROWSE.format(app_slug=self.app_slug, bucket=self.bucket)
        params = build_params(
            prefix=prefix,
            page=page,
            page_size=page_size,
            sort=sort,
            order=order,
        )
        qs = build_query_string(params)
        response = self._http.get(path + qs)
        return self._extract_data(response)

    def copy_object(
        self, source_path: str, destination_path: str, destination_bucket: Optional[str] = None
    ) -> StorageFile:
        """
        Copy an object to a new location.

        Args:
            source_path: Path to source object
            destination_path: Path for copied object
            destination_bucket: Target bucket slug (defaults to current bucket)

        Returns:
            StorageFile dict with new object metadata

        Examples:
            # Copy within same bucket
            new_obj = storage.from_("my-bucket").copy_object(
                "users/123/avatar.jpg",
                "users/456/avatar.jpg"
            )

            # Copy to different bucket
            new_obj = storage.from_("uploads").copy_object(
                "temp/file.pdf",
                "archive/file.pdf",
                destination_bucket="archives"
            )
        """
        path = _STORAGE_COPY.format(app_slug=self.app_slug, bucket=self.bucket)

        body: dict[str, Any] = {"source_path": source_path, "destination_path": destination_path}

        if destination_bucket:
            body["destination_bucket"] = destination_bucket

        response = self._http.post(path, json=body)
        return self._extract_data(response)

    def move_object(self, source_path: str, destination_path: str) -> StorageFile:
        """
        Move or rename an object within the bucket.

        WARNING: This copies the file to new location then deletes original.
        Large files may take several seconds.

        Args:
            source_path: Path to source object
            destination_path: New path for object

        Returns:
            StorageFile dict with updated object metadata

        Example:
            obj = storage.from_("my-bucket").move_object(
                "temp/document.pdf",
                "archive/2024/document.pdf"
            )
        """
        path = _STORAGE_MOVE.format(app_slug=self.app_slug, bucket=self.bucket)

        body = {"source_path": source_path, "destination_path": destination_path}

        response = self._http.post(path, json=body)
        return self._extract_data(response)


class StorageModule(BaseModule):
    """Storage API operations."""

    def __init__(self, client: SyncClient) -> None:
        """Initialize StorageModule."""
        self.client = client
        super().__init__(client._http_client, client._config)

    def from_(self, bucket: str, app_slug: Optional[str] = None) -> StorageQueryBuilder:
        """Select a bucket for storage operations."""
        return StorageQueryBuilder(self.client, bucket, app_slug)

    def list_buckets(
        self,
        *,
        search: Optional[str] = None,
        visibility: Optional[str] = None,
        app_category: Optional[str] = None,
        ordering: Optional[str] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        app_slug: Optional[str] = None,
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
            response = storage.list_buckets()
            buckets = response["results"]

            # Search and filter
            response = storage.list_buckets(
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
        params = build_params(
            search=search,
            visibility=visibility,
            app_category=app_category,
            ordering=ordering,
            page=page,
            page_size=page_size,
        )

        response = self._http.get(path, params=params)
        return self._extract_data(response)

    def create_bucket(
        self,
        name: str,
        *,
        slug: Optional[str] = None,
        visibility: str = "private",
        file_size_limit: Optional[int] = None,
        allowed_mime_types: Optional[list[str]] = None,
        app_category: Optional[str] = None,
        max_size_bytes: Optional[int] = None,
        max_objects: Optional[int] = None,
        app_slug: Optional[str] = None,
    ) -> Bucket:
        """
        Create a new storage bucket.

        Args:
            name: Bucket display name (required)
            slug: URL-friendly identifier (auto-generated if not provided)
            visibility: "public" or "private" (default: "private")
            file_size_limit: Max file size in bytes
            allowed_mime_types: List of allowed MIME types (e.g., ["image/*", "video/*"])
            app_category: "assets" or "attachments"
            max_size_bytes: Maximum total storage size for bucket in bytes (quota limit)
            max_objects: Maximum number of objects allowed in bucket (quota limit)
            app_slug: Override app_slug

        Returns:
            Bucket dict with new bucket metadata

        Examples:
            # Simple bucket
            bucket = storage.create_bucket("My Images")

            # With options
            bucket = storage.create_bucket(
                "User Uploads",
                slug="user-uploads",
                visibility="private",
                file_size_limit=10485760,  # 10MB per file
                allowed_mime_types=["image/jpeg", "image/png"],
                app_category="assets",
                max_size_bytes=1073741824,  # 1GB total bucket size limit
                max_objects=1000  # Max 1000 files
            )
        """
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _STORAGE_BUCKETS.format(app_slug=app_slug)
        body: dict[str, Any] = {
            "name": name,
            "app_category": app_category
            or "attachments",  # Default to 'attachments' if not provided
        }

        if slug:
            body["slug"] = slug
        if visibility:
            body["visibility"] = visibility
        if file_size_limit is not None:
            body["file_size_limit"] = file_size_limit
        if allowed_mime_types:
            body["allowed_mime_types"] = allowed_mime_types
        if max_size_bytes is not None:
            body["max_size_bytes"] = max_size_bytes
        if max_objects is not None:
            body["max_objects"] = max_objects

        response = self._http.post(path, json=body)
        return self._extract_data(response)

    def get_bucket(self, slug: str, *, app_slug: Optional[str] = None) -> Bucket:
        """
        Get a specific bucket by slug.

        Args:
            slug: Bucket slug identifier
            app_slug: Override app_slug

        Returns:
            Bucket dict with bucket metadata

        Example:
            bucket = storage.get_bucket("my-bucket")
        """
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _STORAGE_BUCKET.format(app_slug=app_slug, slug=slug)
        response = self._http.get(path)
        return self._extract_data(response)

    def update_bucket(
        self,
        slug: str,
        *,
        name: Optional[str] = None,
        visibility: Optional[str] = None,
        file_size_limit: Optional[int] = None,
        allowed_mime_types: Optional[list[str]] = None,
        app_category: Optional[str] = None,
        max_size_bytes: Optional[int] = None,
        max_objects: Optional[int] = None,
        app_slug: Optional[str] = None,
    ) -> Bucket:
        """
        Update bucket settings.

        Args:
            slug: Bucket slug identifier
            name: New bucket name
            visibility: "public" or "private"
            file_size_limit: New max file size in bytes
            allowed_mime_types: New list of allowed MIME types
            app_category: "assets" or "attachments"
            max_size_bytes: Maximum total storage size for bucket in bytes (quota limit)
            max_objects: Maximum number of objects allowed in bucket (quota limit)
            app_slug: Override app_slug

        Returns:
            Bucket dict with updated bucket metadata

        Example:
            bucket = storage.update_bucket(
                "my-bucket",
                visibility="public",
                file_size_limit=104857600,  # 100MB per file
                max_size_bytes=10737418240,  # 10GB total bucket size
                max_objects=5000  # Max 5000 files
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
        if max_size_bytes is not None:
            body["max_size_bytes"] = max_size_bytes
        if max_objects is not None:
            body["max_objects"] = max_objects

        response = self._http.patch(path, json=body)
        return self._extract_data(response)

    def delete_bucket(self, slug: str, *, app_slug: Optional[str] = None) -> None:
        """
        Delete a bucket and all its objects.

        WARNING: This permanently deletes all files in the bucket.

        Args:
            slug: Bucket slug identifier
            app_slug: Override app_slug

        Example:
            storage.delete_bucket("old-bucket")
        """
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _STORAGE_BUCKET.format(app_slug=app_slug, slug=slug)
        self._http.delete(path)
