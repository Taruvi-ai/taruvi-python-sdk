"""Tests for storage API enhancements (bucket management and object operations)."""

import pytest
from unittest.mock import Mock, AsyncMock
from taruvi.modules.storage import StorageModule, SyncStorageModule


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_config():
    """Mock configuration."""
    config = Mock()
    config.app_slug = "test-app"
    config.api_url = "https://api.test.com"
    config.headers = {"Authorization": "Bearer test-key"}
    return config


@pytest.fixture
def mock_async_http():
    """Mock async HTTP client."""
    http = Mock()
    http.get = AsyncMock()
    http.post = AsyncMock()
    http.patch = AsyncMock()
    http.delete = AsyncMock()
    return http


@pytest.fixture
def mock_sync_http():
    """Mock sync HTTP client."""
    http = Mock()
    http.get = Mock()
    http.post = Mock()
    http.patch = Mock()
    http.delete = Mock()
    return http


@pytest.fixture
def async_storage_module(mock_config, mock_async_http):
    """Create async storage module with mocked dependencies."""
    client = Mock()
    client._http_client = mock_async_http
    client._config = mock_config
    return StorageModule(client)


@pytest.fixture
def sync_storage_module(mock_config, mock_sync_http):
    """Create sync storage module with mocked dependencies."""
    client = Mock()
    client._http = mock_sync_http
    client._config = mock_config
    return SyncStorageModule(client)


# ============================================================================
# Bucket Management Tests - Async
# ============================================================================

@pytest.mark.asyncio
async def test_list_buckets_async_simple(async_storage_module, mock_async_http):
    """Test list_buckets with no filters (async)."""
    mock_response = {
        "data": {
            "count": 2,
            "results": [
                {"id": 1, "slug": "bucket-1", "name": "Bucket 1"},
                {"id": 2, "slug": "bucket-2", "name": "Bucket 2"}
            ]
        }
    }
    mock_async_http.get.return_value = mock_response

    result = await async_storage_module.list_buckets()

    assert result == mock_response["data"]
    mock_async_http.get.assert_called_once_with(
        "/api/apps/test-app/storage/buckets/",
        params={}
    )


@pytest.mark.asyncio
async def test_list_buckets_async_with_filters(async_storage_module, mock_async_http):
    """Test list_buckets with all filters (async)."""
    mock_response = {"data": {"count": 1, "results": []}}
    mock_async_http.get.return_value = mock_response

    result = await async_storage_module.list_buckets(
        search="images",
        visibility="public",
        app_category="assets",
        ordering="-created_at",
        page=2,
        page_size=20
    )

    assert result == mock_response["data"]
    mock_async_http.get.assert_called_once_with(
        "/api/apps/test-app/storage/buckets/",
        params={
            "search": "images",
            "visibility": "public",
            "app_category": "assets",
            "ordering": "-created_at",
            "page": 2,
            "page_size": 20
        }
    )


@pytest.mark.asyncio
async def test_create_bucket_async_simple(async_storage_module, mock_async_http):
    """Test create_bucket with minimal params (async)."""
    mock_response = {
        "data": {
            "id": 1,
            "slug": "my-bucket",
            "name": "My Bucket",
            "visibility": "private"
        }
    }
    mock_async_http.post.return_value = mock_response

    result = await async_storage_module.create_bucket("My Bucket")

    assert result == mock_response["data"]
    mock_async_http.post.assert_called_once_with(
        "/api/apps/test-app/storage/buckets/",
        json={"name": "My Bucket", "visibility": "private"}
    )


@pytest.mark.asyncio
async def test_create_bucket_async_with_options(async_storage_module, mock_async_http):
    """Test create_bucket with all options (async)."""
    mock_response = {"data": {"id": 1, "slug": "user-uploads"}}
    mock_async_http.post.return_value = mock_response

    result = await async_storage_module.create_bucket(
        "User Uploads",
        slug="user-uploads",
        visibility="public",
        file_size_limit=10485760,
        allowed_mime_types=["image/*", "video/*"],
        app_category="assets"
    )

    assert result == mock_response["data"]
    mock_async_http.post.assert_called_once_with(
        "/api/apps/test-app/storage/buckets/",
        json={
            "name": "User Uploads",
            "slug": "user-uploads",
            "visibility": "public",
            "file_size_limit": 10485760,
            "allowed_mime_types": ["image/*", "video/*"],
            "app_category": "assets"
        }
    )


@pytest.mark.asyncio
async def test_get_bucket_async(async_storage_module, mock_async_http):
    """Test get_bucket (async)."""
    mock_response = {
        "data": {
            "id": 1,
            "slug": "my-bucket",
            "name": "My Bucket"
        }
    }
    mock_async_http.get.return_value = mock_response

    result = await async_storage_module.get_bucket("my-bucket")

    assert result == mock_response["data"]
    mock_async_http.get.assert_called_once_with(
        "/api/apps/test-app/storage/buckets/my-bucket/"
    )


@pytest.mark.asyncio
async def test_update_bucket_async_partial(async_storage_module, mock_async_http):
    """Test update_bucket with partial fields (async)."""
    mock_response = {
        "data": {
            "id": 1,
            "slug": "my-bucket",
            "visibility": "public"
        }
    }
    mock_async_http.patch.return_value = mock_response

    result = await async_storage_module.update_bucket(
        "my-bucket",
        visibility="public",
        file_size_limit=104857600
    )

    assert result == mock_response["data"]
    mock_async_http.patch.assert_called_once_with(
        "/api/apps/test-app/storage/buckets/my-bucket/",
        json={
            "visibility": "public",
            "file_size_limit": 104857600
        }
    )


@pytest.mark.asyncio
async def test_delete_bucket_async(async_storage_module, mock_async_http):
    """Test delete_bucket (async)."""
    mock_async_http.delete.return_value = None

    result = await async_storage_module.delete_bucket("old-bucket")

    assert result is None
    mock_async_http.delete.assert_called_once_with(
        "/api/apps/test-app/storage/buckets/old-bucket/"
    )


# ============================================================================
# Object Operations Tests - Async
# ============================================================================

@pytest.mark.asyncio
async def test_copy_object_async_same_bucket(async_storage_module, mock_async_http, mock_config):
    """Test copy_object within same bucket (async)."""
    query_builder = async_storage_module.from_("my-bucket")

    mock_response = {
        "data": {
            "id": 2,
            "file_path": "users/456/avatar.jpg",
            "size": 102400
        }
    }
    mock_async_http.post.return_value = mock_response

    result = await query_builder.copy_object(
        "users/123/avatar.jpg",
        "users/456/avatar.jpg"
    )

    assert result == mock_response["data"]
    mock_async_http.post.assert_called_once_with(
        "/api/apps/test-app/storage/buckets/my-bucket/objects/copy/",
        json={
            "source_path": "users/123/avatar.jpg",
            "destination_path": "users/456/avatar.jpg"
        }
    )


@pytest.mark.asyncio
async def test_copy_object_async_different_bucket(async_storage_module, mock_async_http):
    """Test copy_object to different bucket (async)."""
    query_builder = async_storage_module.from_("uploads")

    mock_response = {"data": {"id": 2, "file_path": "archive/file.pdf"}}
    mock_async_http.post.return_value = mock_response

    result = await query_builder.copy_object(
        "temp/file.pdf",
        "archive/file.pdf",
        destination_bucket="archives"
    )

    assert result == mock_response["data"]
    mock_async_http.post.assert_called_once_with(
        "/api/apps/test-app/storage/buckets/uploads/objects/copy/",
        json={
            "source_path": "temp/file.pdf",
            "destination_path": "archive/file.pdf",
            "destination_bucket": "archives"
        }
    )


@pytest.mark.asyncio
async def test_move_object_async(async_storage_module, mock_async_http):
    """Test move_object (async)."""
    query_builder = async_storage_module.from_("my-bucket")

    mock_response = {
        "data": {
            "id": 1,
            "file_path": "archive/2024/document.pdf"
        }
    }
    mock_async_http.post.return_value = mock_response

    result = await query_builder.move_object(
        "temp/document.pdf",
        "archive/2024/document.pdf"
    )

    assert result == mock_response["data"]
    mock_async_http.post.assert_called_once_with(
        "/api/apps/test-app/storage/buckets/my-bucket/objects/move/",
        json={
            "source_path": "temp/document.pdf",
            "destination_path": "archive/2024/document.pdf"
        }
    )


# ============================================================================
# Bucket Management Tests - Sync
# ============================================================================

def test_list_buckets_sync_simple(sync_storage_module, mock_sync_http):
    """Test list_buckets with no filters (sync)."""
    mock_response = {
        "data": {
            "count": 2,
            "results": [
                {"id": 1, "slug": "bucket-1", "name": "Bucket 1"},
                {"id": 2, "slug": "bucket-2", "name": "Bucket 2"}
            ]
        }
    }
    mock_sync_http.get.return_value = mock_response

    result = sync_storage_module.list_buckets()

    assert result == mock_response["data"]
    mock_sync_http.get.assert_called_once_with(
        "/api/apps/test-app/storage/buckets/",
        params={}
    )


def test_list_buckets_sync_with_filters(sync_storage_module, mock_sync_http):
    """Test list_buckets with all filters (sync)."""
    mock_response = {"data": {"count": 1, "results": []}}
    mock_sync_http.get.return_value = mock_response

    result = sync_storage_module.list_buckets(
        search="images",
        visibility="public",
        app_category="assets",
        ordering="-created_at",
        page=2,
        page_size=20
    )

    assert result == mock_response["data"]
    mock_sync_http.get.assert_called_once_with(
        "/api/apps/test-app/storage/buckets/",
        params={
            "search": "images",
            "visibility": "public",
            "app_category": "assets",
            "ordering": "-created_at",
            "page": 2,
            "page_size": 20
        }
    )


def test_create_bucket_sync_simple(sync_storage_module, mock_sync_http):
    """Test create_bucket with minimal params (sync)."""
    mock_response = {
        "data": {
            "id": 1,
            "slug": "my-bucket",
            "name": "My Bucket",
            "visibility": "private"
        }
    }
    mock_sync_http.post.return_value = mock_response

    result = sync_storage_module.create_bucket("My Bucket")

    assert result == mock_response["data"]
    mock_sync_http.post.assert_called_once_with(
        "/api/apps/test-app/storage/buckets/",
        json={"name": "My Bucket", "visibility": "private"}
    )


def test_create_bucket_sync_with_options(sync_storage_module, mock_sync_http):
    """Test create_bucket with all options (sync)."""
    mock_response = {"data": {"id": 1, "slug": "user-uploads"}}
    mock_sync_http.post.return_value = mock_response

    result = sync_storage_module.create_bucket(
        "User Uploads",
        slug="user-uploads",
        visibility="public",
        file_size_limit=10485760,
        allowed_mime_types=["image/*", "video/*"],
        app_category="assets"
    )

    assert result == mock_response["data"]
    mock_sync_http.post.assert_called_once_with(
        "/api/apps/test-app/storage/buckets/",
        json={
            "name": "User Uploads",
            "slug": "user-uploads",
            "visibility": "public",
            "file_size_limit": 10485760,
            "allowed_mime_types": ["image/*", "video/*"],
            "app_category": "assets"
        }
    )


def test_get_bucket_sync(sync_storage_module, mock_sync_http):
    """Test get_bucket (sync)."""
    mock_response = {
        "data": {
            "id": 1,
            "slug": "my-bucket",
            "name": "My Bucket"
        }
    }
    mock_sync_http.get.return_value = mock_response

    result = sync_storage_module.get_bucket("my-bucket")

    assert result == mock_response["data"]
    mock_sync_http.get.assert_called_once_with(
        "/api/apps/test-app/storage/buckets/my-bucket/"
    )


def test_update_bucket_sync_partial(sync_storage_module, mock_sync_http):
    """Test update_bucket with partial fields (sync)."""
    mock_response = {
        "data": {
            "id": 1,
            "slug": "my-bucket",
            "visibility": "public"
        }
    }
    mock_sync_http.patch.return_value = mock_response

    result = sync_storage_module.update_bucket(
        "my-bucket",
        visibility="public",
        file_size_limit=104857600
    )

    assert result == mock_response["data"]
    mock_sync_http.patch.assert_called_once_with(
        "/api/apps/test-app/storage/buckets/my-bucket/",
        json={
            "visibility": "public",
            "file_size_limit": 104857600
        }
    )


def test_delete_bucket_sync(sync_storage_module, mock_sync_http):
    """Test delete_bucket (sync)."""
    mock_sync_http.delete.return_value = None

    result = sync_storage_module.delete_bucket("old-bucket")

    assert result is None
    mock_sync_http.delete.assert_called_once_with(
        "/api/apps/test-app/storage/buckets/old-bucket/"
    )


# ============================================================================
# Object Operations Tests - Sync
# ============================================================================

def test_copy_object_sync_same_bucket(sync_storage_module, mock_sync_http):
    """Test copy_object within same bucket (sync)."""
    query_builder = sync_storage_module.from_("my-bucket")

    mock_response = {
        "data": {
            "id": 2,
            "file_path": "users/456/avatar.jpg",
            "size": 102400
        }
    }
    mock_sync_http.post.return_value = mock_response

    result = query_builder.copy_object(
        "users/123/avatar.jpg",
        "users/456/avatar.jpg"
    )

    assert result == mock_response["data"]
    mock_sync_http.post.assert_called_once_with(
        "/api/apps/test-app/storage/buckets/my-bucket/objects/copy/",
        json={
            "source_path": "users/123/avatar.jpg",
            "destination_path": "users/456/avatar.jpg"
        }
    )


def test_copy_object_sync_different_bucket(sync_storage_module, mock_sync_http):
    """Test copy_object to different bucket (sync)."""
    query_builder = sync_storage_module.from_("uploads")

    mock_response = {"data": {"id": 2, "file_path": "archive/file.pdf"}}
    mock_sync_http.post.return_value = mock_response

    result = query_builder.copy_object(
        "temp/file.pdf",
        "archive/file.pdf",
        destination_bucket="archives"
    )

    assert result == mock_response["data"]
    mock_sync_http.post.assert_called_once_with(
        "/api/apps/test-app/storage/buckets/uploads/objects/copy/",
        json={
            "source_path": "temp/file.pdf",
            "destination_path": "archive/file.pdf",
            "destination_bucket": "archives"
        }
    )


def test_move_object_sync(sync_storage_module, mock_sync_http):
    """Test move_object (sync)."""
    query_builder = sync_storage_module.from_("my-bucket")

    mock_response = {
        "data": {
            "id": 1,
            "file_path": "archive/2024/document.pdf"
        }
    }
    mock_sync_http.post.return_value = mock_response

    result = query_builder.move_object(
        "temp/document.pdf",
        "archive/2024/document.pdf"
    )

    assert result == mock_response["data"]
    mock_sync_http.post.assert_called_once_with(
        "/api/apps/test-app/storage/buckets/my-bucket/objects/move/",
        json={
            "source_path": "temp/document.pdf",
            "destination_path": "archive/2024/document.pdf"
        }
    )


# ============================================================================
# Error Handling Tests
# ============================================================================

@pytest.mark.asyncio
async def test_list_buckets_async_missing_app_slug(mock_async_http):
    """Test list_buckets raises error when app_slug is missing (async)."""
    client = Mock()
    client._http_client = mock_async_http
    config = Mock()
    config.app_slug = None
    client._config = config

    storage = StorageModule(client)

    with pytest.raises(ValueError, match="app_slug is required"):
        await storage.list_buckets()


def test_list_buckets_sync_missing_app_slug(mock_sync_http):
    """Test list_buckets raises error when app_slug is missing (sync)."""
    client = Mock()
    client._http = mock_sync_http
    config = Mock()
    config.app_slug = None
    client._config = config

    storage = SyncStorageModule(client)

    with pytest.raises(ValueError, match="app_slug is required"):
        storage.list_buckets()


@pytest.mark.asyncio
async def test_create_bucket_async_missing_app_slug(mock_async_http):
    """Test create_bucket raises error when app_slug is missing (async)."""
    client = Mock()
    client._http_client = mock_async_http
    config = Mock()
    config.app_slug = None
    client._config = config

    storage = StorageModule(client)

    with pytest.raises(ValueError, match="app_slug is required"):
        await storage.create_bucket("My Bucket")


def test_create_bucket_sync_missing_app_slug(mock_sync_http):
    """Test create_bucket raises error when app_slug is missing (sync)."""
    client = Mock()
    client._http = mock_sync_http
    config = Mock()
    config.app_slug = None
    client._config = config

    storage = SyncStorageModule(client)

    with pytest.raises(ValueError, match="app_slug is required"):
        storage.create_bucket("My Bucket")
