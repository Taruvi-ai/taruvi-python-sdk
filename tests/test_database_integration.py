"""Database acceptance against the explicitly owned live fixture.

Both public clients exercise PostgreSQL persistence, query windows, conflict
handling and upserts. Errors and assertion failures fail the run; only the
central explicit opt-in gate skips these cases.
"""

import inspect
from contextlib import asynccontextmanager
from uuid import uuid4

import pytest

from taruvi.exceptions import ConflictError, NotFoundError, ValidationError

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def resolve(value):
    return await value if inspect.isawaitable(value) else value


@pytest.fixture(params=["sync", "async"])
def database_module(request, sync_database_module, async_database_module):
    return sync_database_module if request.param == "sync" else async_database_module


@asynccontextmanager
async def owned_records(module, table):
    ids = set()
    try:
        yield ids
    finally:
        for record_id in ids:
            try:
                await resolve(module.delete(table, record_id))
            except NotFoundError:
                # A lifecycle may already have deleted this owned record.
                pass


async def create_rows(module, table, payload, ids):
    rows = await resolve(module.create(table, payload))
    assert isinstance(rows, list)
    ids.update(row["id"] for row in rows)
    assert len(rows) == (len(payload) if isinstance(payload, list) else 1)
    return rows


async def test_record_lifecycle_persists_changes_and_returns_204(database_module, live_resources):
    table = live_resources["database"]["table_name"]
    marker = uuid4().hex
    payload = {"name": f"create-{marker}", "email": f"{marker}@example.invalid"}
    async with owned_records(database_module, table) as ids:
        row = (await create_rows(database_module, table, payload, ids))[0]
        assert {key: row[key] for key in payload} == payload
        saved = await resolve(database_module.get(table, row["id"]))
        assert saved["id"] == row["id"]
        assert saved["email"] == payload["email"]

        update = {"name": f"updated-{marker}", "description": "persisted patch"}
        changed = await resolve(database_module.update(table, row["id"], update))
        assert changed["id"] == row["id"]
        saved = await resolve(database_module.from_(table).get(row["id"]).first())
        assert {key: saved[key] for key in update} == update
        assert saved["email"] == payload["email"]

        assert await resolve(database_module.delete(table, row["id"])) is None
        ids.remove(row["id"])
        with pytest.raises(NotFoundError):
            await resolve(database_module.get(table, row["id"]))


async def test_bulk_query_filter_windows_and_count(database_module, live_resources):
    table = live_resources["database"]["table_name"]
    marker = uuid4().hex
    payload = [
        {"name": f"item-{i}", "email": f"{marker}-{i}@example.invalid", "description": marker}
        for i in range(5)
    ]
    async with owned_records(database_module, table) as ids:
        rows = await create_rows(database_module, table, payload, ids)
        outsider = {"name": "outside", "email": f"{marker}-outside@example.invalid"}
        await create_rows(database_module, table, outsider, ids)

        changed = await resolve(
            database_module.update(
                table,
                [{"id": row["id"], "name": "bulk-updated"} for row in rows[:2]],
            )
        )
        assert isinstance(changed, list)
        assert {row["id"] for row in changed} == {row["id"] for row in rows[:2]}
        for row in rows[:2]:
            assert (await resolve(database_module.get(table, row["id"])))["name"] == "bulk-updated"

        query = database_module.from_(table).filter("description", "eq", marker).sort("email")
        pages = [await resolve(query.page_size(2).page(page).execute()) for page in (1, 2, 3)]
        assert [len(page["data"]) for page in pages] == [2, 2, 1]
        assert [page["total"] for page in pages] == [5, 5, 5]
        assert [row["email"] for page in pages for row in page["data"]] == [
            row["email"] for row in payload
        ]
        assert await resolve(query.count()) == 5
        assert (await resolve(query.page(2).first()))["email"] == payload[2]["email"]

        selected = (
            database_module.from_(table)
            .filter({"or": [{"email": payload[1]["email"]}, {"email": payload[3]["email"]}]})
            .sort("email")
        )
        result = await resolve(selected.execute())
        assert [row["email"] for row in result["data"]] == [
            payload[1]["email"],
            payload[3]["email"],
        ]
        assert {row["id"] for row in rows} == {row["id"] for page in pages for row in page["data"]}


async def test_upsert_preserves_conflict_identity_and_persists_new_row(
    database_module, live_resources
):
    table = live_resources["database"]["table_name"]
    marker = uuid4().hex
    payload = {"name": "original", "email": f"{marker}@example.invalid"}
    async with owned_records(database_module, table) as ids:
        original = (await create_rows(database_module, table, payload, ids))[0]
        new_email = f"{marker}-new@example.invalid"
        result = await resolve(
            database_module.from_(table)
            .upsert(
                [{**payload, "name": "changed"}, {"name": "inserted", "email": new_email}],
                unique_fields=["email"],
            )
            .execute()
        )
        assert result["status"] == "success"
        rows = result["data"]["records"]
        ids.update(row["id"] for row in rows)
        assert result["data"]["count"] == 2
        assert rows[0]["id"] == original["id"]
        assert rows[1]["id"] != original["id"]
        assert (await resolve(database_module.get(table, original["id"])))["name"] == "changed"
        assert (await resolve(database_module.get(table, rows[1]["id"])))["email"] == new_email


async def test_database_invalid_payload_and_unique_conflict_fail(database_module, live_resources):
    table = live_resources["database"]["table_name"]
    payload = {"name": "unique", "email": f"{uuid4().hex}@example.invalid"}
    async with owned_records(database_module, table) as ids:
        original = (await create_rows(database_module, table, payload, ids))[0]
        with pytest.raises(ConflictError):
            await resolve(database_module.create(table, payload))
        with pytest.raises(ValidationError):
            await resolve(database_module.create(table, {}))
        saved = await resolve(database_module.get(table, original["id"]))
        assert saved["name"] == payload["name"]
        with pytest.raises(NotFoundError):
            await resolve(database_module.from_(f"absent-{uuid4().hex}").execute())
