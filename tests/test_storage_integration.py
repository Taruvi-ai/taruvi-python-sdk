"""Owned S3/MinIO acceptance through both public HTTP clients.

Exercise actual binary storage and database inventory together. Batch partial
results are inspected explicitly; an inaccessible bucket or provider failure is
never converted into a skip.
"""

import inspect
from contextlib import asynccontextmanager
from io import BytesIO
from uuid import uuid4

import pytest

from taruvi.exceptions import NotFoundError, ValidationError

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def resolve(value):
    return await value if inspect.isawaitable(value) else value


@pytest.fixture(params=["sync", "async"])
def storage_module(request, sync_storage_module, async_storage_module):
    return sync_storage_module if request.param == "sync" else async_storage_module


@asynccontextmanager
async def owned_objects(bucket):
    paths = set()
    try:
        yield paths
    finally:
        if paths:
            result = await resolve(bucket.delete(sorted(paths)))
            assert all(item["error"] == "Object not found" for item in result["failed"]), result
            assert result["deleted_count"] + len(result["failed"]) == len(paths)


def assert_uploaded(result, paths):
    assert result["uploaded_count"] == len(paths)
    assert result["failed_count"] == 0
    assert result["failed"] == []
    assert result["total"] == len(paths)
    assert [entry["path"] for entry in result["successful"]] == paths
    for index, entry in enumerate(result["successful"]):
        assert entry["index"] == index
        assert entry["object"]["file_path"] == paths[index]
        assert entry["object"]["storage_provider"] == "s3"


async def test_binary_roundtrip_metadata_copy_move_and_delete(storage_module, live_resources):
    resource = live_resources["storage"]
    bucket = storage_module.from_(resource["bucket_slug"])
    prefix = f'{resource["prefix"]}{uuid4().hex}/'
    source, copied, moved = (
        f"{prefix}{name}" for name in ("café #1.bin", "copied.bin", "moved.bin")
    )
    content = b"\x00\xff\x10SDK binary roundtrip\r\n"
    async with owned_objects(bucket) as owned:
        owned.add(source)
        result = await resolve(
            bucket.upload(
                files=[("source.bin", BytesIO(content), "application/octet-stream")],
                paths=[source],
                metadatas=[{"purpose": "live-acceptance"}],
            )
        )
        assert_uploaded(result, [source])
        assert result["successful"][0]["object"]["size"] == len(content)
        assert await resolve(bucket.download(source)) == content

        metadata = {"reviewed": True, "revision": 2}
        changed = await resolve(bucket.update(source, metadata=metadata, visibility="private"))
        assert changed["metadata"] == metadata
        inventory = await resolve(bucket.filter(prefix=prefix).list())
        assert inventory["total"] == 1
        assert inventory["data"][0]["metadata"] == metadata
        assert inventory["data"][0]["visibility"] == "private"

        owned.add(copied)
        copy = await resolve(bucket.copy_object(source, copied))
        assert copy["file_path"] == copied
        assert await resolve(bucket.download(copied)) == content
        owned.add(moved)
        move = await resolve(bucket.move_object(copied, moved))
        assert move["file_path"] == moved
        assert await resolve(bucket.download(moved)) == content
        with pytest.raises(NotFoundError):
            await resolve(bucket.download(copied))
        owned.remove(copied)

        deleted = await resolve(bucket.delete([source, moved]))
        assert deleted["deleted_count"] == 2
        assert deleted["failed"] == []
        owned.difference_update([source, moved])
        assert (await resolve(bucket.filter(prefix=prefix).list()))["total"] == 0
        with pytest.raises(NotFoundError):
            await resolve(bucket.download(source))


async def test_folder_browse_pagination_sorting_and_list_filters(storage_module, live_resources):
    resource = live_resources["storage"]
    bucket = storage_module.from_(resource["bucket_slug"])
    prefix = f'{resource["prefix"]}{uuid4().hex}/'
    paths = [f"{prefix}{name}" for name in ("a.txt", "b.txt", "nested/c.txt")]
    async with owned_objects(bucket) as owned:
        owned.update(paths)
        result = await resolve(
            bucket.upload(
                files=[
                    (name, BytesIO(name.encode()), "text/plain")
                    for name in ("a.txt", "b.txt", "c.txt")
                ],
                paths=paths,
            )
        )
        assert_uploaded(result, paths)
        pages = [
            await resolve(
                bucket.browse(prefix=prefix, page=page, page_size=2, sort="name", order="asc")
            )
            for page in (1, 2)
        ]
        assert pages[0]["prefix"] == prefix
        assert [page["has_next"] for page in pages] == [True, False]
        assert [page["page"] for page in pages] == [1, 2]
        assert [obj["path"] for page in pages for obj in page["objects"]] == paths[:2]
        assert [folder for page in pages for folder in page["folders"]] == [
            {"type": "folder", "name": "nested", "path": f"{prefix}nested/"}
        ]
        nested = await resolve(bucket.browse(prefix=f"{prefix}nested/"))
        assert nested["folders"] == []
        assert [obj["path"] for obj in nested["objects"]] == paths[2:]
        descending = await resolve(bucket.browse(prefix=prefix, sort="name", order="desc"))
        assert [obj["name"] for obj in descending["objects"]] == ["b.txt", "a.txt"]
        inventory = await resolve(bucket.filter(prefix=prefix, mimetype="text/plain").list())
        assert inventory["total"] == 3
        assert {obj["file_path"] for obj in inventory["data"]} == set(paths)
        empty = await resolve(bucket.browse(prefix=f"{prefix}missing/"))
        assert empty["objects"] == empty["folders"] == []
        assert empty["has_next"] is False


async def test_batch_partial_results_and_validation_do_not_hide_failures(
    storage_module, live_resources
):
    resource = live_resources["storage"]
    bucket = storage_module.from_(resource["bucket_slug"])
    prefix = f'{resource["prefix"]}{uuid4().hex}/'
    good, invalid, oversized, missing = (
        f"{prefix}{name}" for name in ("good.txt", "invalid.txt", "oversized.txt", "absent.txt")
    )
    async with owned_objects(bucket) as owned:
        owned.update([good, invalid, oversized])
        result = await resolve(
            bucket.upload(
                files=[
                    ("good.txt", BytesIO(b"good")),
                    ("invalid.txt", BytesIO(b"invalid")),
                    ("oversized.txt", BytesIO(b"x" * 2048)),
                ],
                paths=[good, invalid, oversized],
                metadatas=[{"purpose": "accepted"}, {"large": "x" * 2050}, {}],
            )
        )
        assert result["total"] == 3
        assert result["uploaded_count"] == 1
        assert result["failed_count"] == 2
        assert [item["path"] for item in result["successful"]] == [good]
        assert result["failed"][0]["path"] == invalid
        assert result["failed"][0]["index"] == 1
        assert "2KB" in result["failed"][0]["error"]
        assert result["failed"][1]["path"] == oversized
        assert result["failed"][1]["index"] == 2
        assert "bucket limit" in result["failed"][1]["error"]
        assert await resolve(bucket.download(good)) == b"good"
        with pytest.raises(NotFoundError):
            await resolve(bucket.download(invalid))
        deleted = await resolve(bucket.delete([good, missing]))
        assert deleted["deleted_count"] == 1
        assert deleted["failed"] == [{"path": missing, "error": "Object not found"}]
        owned.remove(good)
        with pytest.raises(ValidationError):
            await resolve(bucket.upload(files=[("mismatch.txt", BytesIO(b"data"))], paths=[]))
