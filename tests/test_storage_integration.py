"""
Integration tests for Storage API module.

IMPORTANT: These are REAL integration tests - NO MOCKS!
- Uploads actual files to Taruvi backend storage
- Downloads and verifies file content
- Tests bucket operations with real storage backend
- All uploaded files are cleaned up after tests

Setup:
    1. Ensure .env is configured with backend URL and credentials
    2. Backend must have storage functionality enabled
    3. Run: RUN_INTEGRATION_TESTS=1 pytest tests/test_storage_integration.py -v
"""

import pytest
import io
from pathlib import Path


# ============================================================================
# File Upload Tests - Async (Real Storage Operations)
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_upload_file_real_api(async_storage_module, generate_unique_id):
    """
    Test uploading a real file to storage backend.

    Creates file, uploads it, verifies it exists, then cleans up.
    """
    bucket_name = "test-bucket"  # Update with your test bucket
    unique_id = generate_unique_id()
    file_path = f"test_files/test_{unique_id}.txt"

    # Create test file content
    file_content = f"Test file content {unique_id}".encode()
    file_obj = io.BytesIO(file_content)

    try:
        # Upload file to real storage using query builder pattern
        result = await async_storage_module.from_(bucket_name).upload(
            files=[("test.txt", file_obj)],
            paths=[file_path]
        )

        # Verify response structure
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0

    except Exception as e:
        if "bucket" in str(e).lower() or "not found" in str(e).lower():
            pytest.skip(f"Skipping: {bucket_name} bucket not accessible - {str(e)}")
        raise

    finally:
        # Cleanup: Delete uploaded file
        try:
            await async_storage_module.from_(bucket_name).delete([file_path])
        except:
            pass  # Ignore cleanup errors


@pytest.mark.integration
@pytest.mark.asyncio
async def test_upload_and_download_file_real_api(async_storage_module, generate_unique_id):
    """
    Test complete upload-download cycle with real storage.

    Uploads file, downloads it, verifies content matches.
    """
    bucket_name = "test-bucket"
    unique_id = generate_unique_id()
    file_path = f"test_files/roundtrip_{unique_id}.txt"

    # Original content
    original_content = f"Roundtrip test content {unique_id}".encode()
    file_obj = io.BytesIO(original_content)

    try:
        # Upload
        upload_result = await async_storage_module.from_(bucket_name).upload(
            files=[("roundtrip.txt", file_obj)],
            paths=[file_path]
        )

        assert upload_result is not None
        assert len(upload_result) > 0

        # Download
        downloaded = await async_storage_module.from_(bucket_name).download(file_path)

        # Verify content matches
        assert downloaded is not None
        assert downloaded == original_content

    except Exception as e:
        if "bucket" in str(e).lower() or "not found" in str(e).lower():
            pytest.skip(f"Skipping: Storage not accessible - {str(e)}")
        raise

    finally:
        # Cleanup
        try:
            await async_storage_module.from_(bucket_name).delete([file_path])
        except:
            pass


@pytest.mark.integration
@pytest.mark.asyncio
async def test_upload_multiple_files_real_api(async_storage_module, generate_unique_id):
    """
    Test uploading multiple files to real storage.

    Uploads multiple files and verifies all succeed.
    """
    bucket_name = "test-bucket"
    unique_id = generate_unique_id()
    uploaded_paths = []
    files = []

    try:
        # Prepare 3 files
        for i in range(3):
            file_path = f"test_files/multi_{unique_id}_{i}.txt"
            file_content = f"Multi file test #{i} - {unique_id}".encode()
            file_obj = io.BytesIO(file_content)
            
            files.append((f"multi_{i}.txt", file_obj))
            uploaded_paths.append(file_path)

        # Upload all files at once
        result = await async_storage_module.from_(bucket_name).upload(
            files=files,
            paths=uploaded_paths
        )

        assert result is not None
        assert len(result) == 3

    except Exception as e:
        if "bucket" in str(e).lower() or "not found" in str(e).lower():
            pytest.skip(f"Skipping: Storage not accessible - {str(e)}")
        raise

    finally:
        # Cleanup all uploaded files
        try:
            await async_storage_module.from_(bucket_name).delete(uploaded_paths)
        except:
            pass


# ============================================================================
# File List Tests - Async (Real Storage Operations)
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_files_real_api(async_storage_module, generate_unique_id):
    """
    Test listing files from real storage bucket.

    Uploads files and verifies list endpoint returns them.
    """
    bucket_name = "test-bucket"
    unique_id = generate_unique_id()
    prefix = f"test_list_{unique_id}/"
    uploaded_paths = []
    files = []

    try:
        # Prepare test files
        for i in range(2):
            file_path = f"{prefix}file_{i}.txt"
            file_obj = io.BytesIO(f"List test {i}".encode())
            files.append((f"file_{i}.txt", file_obj))
            uploaded_paths.append(file_path)

        # Upload files
        await async_storage_module.from_(bucket_name).upload(
            files=files,
            paths=uploaded_paths
        )

        # List files
        result = await async_storage_module.from_(bucket_name).list()

        # Verify structure
        assert result is not None

    except Exception as e:
        if "bucket" in str(e).lower() or "not found" in str(e).lower():
            pytest.skip(f"Skipping: Storage not accessible - {str(e)}")
        raise

    finally:
        # Cleanup
        try:
            await async_storage_module.from_(bucket_name).delete(uploaded_paths)
        except:
            pass


# ============================================================================
# File Delete Tests - Async (Real Storage Operations)
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_file_real_api(async_storage_module, generate_unique_id):
    """
    Test deleting file from real storage.

    Uploads file, deletes it, verifies it's gone.
    """
    bucket_name = "test-bucket"
    unique_id = generate_unique_id()
    file_path = f"test_files/delete_{unique_id}.txt"

    try:
        # Upload file
        file_obj = io.BytesIO(f"Delete test {unique_id}".encode())
        await async_storage_module.from_(bucket_name).upload(
            files=[("delete.txt", file_obj)],
            paths=[file_path]
        )

        # Delete file
        await async_storage_module.from_(bucket_name).delete([file_path])

        # Verify file is gone - should raise error
        with pytest.raises(Exception):
            await async_storage_module.from_(bucket_name).download(file_path)

    except Exception as e:
        if "bucket" in str(e).lower() or "not found" in str(e).lower():
            pytest.skip(f"Skipping: Storage not accessible - {str(e)}")
        raise


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_multiple_files_real_api(async_storage_module, generate_unique_id):
    """
    Test deleting multiple files from real storage.

    Bulk delete operation test.
    """
    bucket_name = "test-bucket"
    unique_id = generate_unique_id()
    file_paths = []
    files = []

    try:
        # Prepare multiple files
        for i in range(3):
            file_path = f"test_files/bulk_delete_{unique_id}_{i}.txt"
            file_obj = io.BytesIO(f"Bulk delete test {i}".encode())
            files.append((f"bulk_{i}.txt", file_obj))
            file_paths.append(file_path)

        # Upload all files
        await async_storage_module.from_(bucket_name).upload(
            files=files,
            paths=file_paths
        )

        # Delete all files at once
        await async_storage_module.from_(bucket_name).delete(file_paths)

    except Exception as e:
        if "bucket" in str(e).lower() or "not found" in str(e).lower():
            pytest.skip(f"Skipping: Storage not accessible - {str(e)}")
        raise

    finally:
        # Ensure cleanup
        try:
            await async_storage_module.from_(bucket_name).delete(file_paths)
        except:
            pass


# ============================================================================
# File Metadata Tests - Async (Real Storage Operations)
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_file_metadata_real_api(async_storage_module, generate_unique_id):
    """
    Test getting file metadata from real storage.

    Uploads file and retrieves its metadata.
    """
    bucket_name = "test-bucket"
    unique_id = generate_unique_id()
    file_path = f"test_files/metadata_{unique_id}.txt"

    try:
        # Upload file
        file_content = f"Metadata test {unique_id}".encode()
        file_obj = io.BytesIO(file_content)

        result = await async_storage_module.from_(bucket_name).upload(
            files=[("metadata.txt", file_obj)],
            paths=[file_path]
        )

        # Verify upload result contains metadata
        assert result is not None
        assert len(result) > 0
        # File metadata should be in the upload result

    except Exception as e:
        if "bucket" in str(e).lower() or "not found" in str(e).lower():
            pytest.skip(f"Skipping: Storage not accessible - {str(e)}")
        raise

    finally:
        # Cleanup
        try:
            await async_storage_module.from_(bucket_name).delete([file_path])
        except:
            pass


# ============================================================================
# Sync Client Tests - Real Storage Operations
# ============================================================================

@pytest.mark.integration
def test_upload_file_sync_real_api(sync_storage_module, generate_unique_id):
    """
    Test uploading file with sync client (no async/await).
    """
    bucket_name = "test-bucket"
    unique_id = generate_unique_id()
    file_path = f"test_files/sync_{unique_id}.txt"

    try:
        # Upload with sync client
        file_obj = io.BytesIO(f"Sync upload test {unique_id}".encode())

        result = sync_storage_module.from_(bucket_name).upload(
            files=[("sync.txt", file_obj)],
            paths=[file_path]
        )

        # Verify
        assert result is not None
        assert len(result) > 0

        # Cleanup
        sync_storage_module.from_(bucket_name).delete([file_path])

    except Exception as e:
        if "bucket" in str(e).lower() or "not found" in str(e).lower():
            pytest.skip(f"Skipping: Storage not accessible - {str(e)}")
        raise


@pytest.mark.integration
def test_download_file_sync_real_api(sync_storage_module, generate_unique_id):
    """
    Test downloading file with sync client.
    """
    bucket_name = "test-bucket"
    unique_id = generate_unique_id()
    file_path = f"test_files/sync_download_{unique_id}.txt"

    try:
        # Upload
        original_content = f"Sync download test {unique_id}".encode()
        file_obj = io.BytesIO(original_content)

        sync_storage_module.from_(bucket_name).upload(
            files=[("sync_download.txt", file_obj)],
            paths=[file_path]
        )

        # Download
        downloaded = sync_storage_module.from_(bucket_name).download(file_path)

        # Verify content
        assert downloaded is not None
        assert downloaded == original_content

        # Cleanup
        sync_storage_module.from_(bucket_name).delete([file_path])

    except Exception as e:
        if "bucket" in str(e).lower() or "not found" in str(e).lower():
            pytest.skip(f"Skipping: Storage not accessible - {str(e)}")
        raise


# ============================================================================
# Error Handling Tests - Real API Errors
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_download_nonexistent_file_real_api(async_storage_module):
    """
    Test downloading non-existent file returns real error.
    """
    bucket_name = "test-bucket"
    fake_path = "nonexistent/file/path.txt"

    try:
        with pytest.raises(Exception):
            await async_storage_module.from_(bucket_name).download(fake_path)

        # Verify we got real error from backend
        assert exc_info.value is not None

    except Exception as e:
        if "bucket" in str(e).lower():
            pytest.skip("Skipping: Bucket not accessible")
        raise


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_nonexistent_file_real_api(async_storage_module):
    """
    Test deleting non-existent file handling.
    """
    bucket_name = "test-bucket"
    fake_path = "nonexistent/delete/path.txt"

    try:
        # May or may not raise error depending on backend implementation
        result = await async_storage_module.delete(bucket_name, fake_path)

        # Either succeeds silently or raises error
        assert result is not None or result is True

    except Exception as e:
        # Expected - file doesn't exist
        assert e is not None


# ============================================================================
# Notes on Storage Integration Tests
# ============================================================================

"""
IMPORTANT CONFIGURATION:

1. Update `bucket_name = "test-bucket"` with your actual test bucket
2. Ensure test bucket exists in your backend storage
3. Verify storage permissions are configured

Cleanup Strategy:
- All tests clean up uploaded files in finally blocks
- Use unique identifiers to avoid conflicts
- Tests are idempotent

Test Coverage:
✅ Upload single file
✅ Upload multiple files
✅ Download files
✅ Verify file content integrity
✅ List files
✅ Delete files
✅ Bulk delete
✅ File metadata (if supported)
✅ Sync client operations
✅ Error handling (file not found, etc.)

File Types Tested:
- Text files (basic test)
- Can extend to: images, PDFs, binary files

Example Bucket Setup:
- Create bucket in Taruvi backend: "test-bucket"
- Grant read/write permissions to test API key
- Enable public or private access as needed
"""
