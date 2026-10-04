"""Owned full-text, vector and hybrid acceptance through actual PostgreSQL.

The vector fixture has scalar ``id``/``name`` fields, a cosine vector(3) column
named ``embedding`` and generated full-text search over ``name``. Tests insert
and remove their own rows; a missing or misconfigured search index fails.
"""

import inspect
from contextlib import asynccontextmanager
from uuid import uuid4

import pytest

from taruvi.exceptions import NotFoundError, ValidationError


async def resolve(value):
    return await value if inspect.isawaitable(value) else value


@pytest.fixture(params=["sync", "async"])
def search_module(request, sync_database_module, async_database_module):
    return sync_database_module if request.param == "sync" else async_database_module


@asynccontextmanager
async def search_rows(module, resources):
    table = resources["database"]["vector_table_name"]
    marker = uuid4().hex
    payload = [
        {"name": f"{marker} invoice guide", "embedding": [1.0, 0.0, 0.0]},
        {"name": f"{marker} tax guide", "embedding": [0.8, 0.6, 0.0]},
        {"name": "outside invoice guide", "embedding": [1.0, 0.0, 0.0]},
        {"name": f"{marker} invoice note", "embedding": [0.0, 1.0, 0.0]},
    ]
    ids = set()
    try:
        rows = await resolve(module.create(table, payload))
        assert isinstance(rows, list)
        ids.update(row["id"] for row in rows)
        assert len(rows) == 4
        yield table, marker, rows
    finally:
        for record_id in ids:
            try:
                await resolve(module.delete(table, record_id))
            except NotFoundError:
                pass


def scoped_query(module, table, marker):
    return module.from_(table).filter("name", "startswith", marker)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_text_filters_pages_and_empty_results(search_module, live_resources):
    async with search_rows(search_module, live_resources) as (table, marker, rows):
        query = scoped_query(search_module, table, marker).search("invoice").sort("id").page_size(1)
        pages = [await resolve(query.page(page).execute()) for page in (1, 2)]
        assert [page["total"] for page in pages] == [2, 2]
        assert [row["id"] for page in pages for row in page["data"]] == [
            rows[0]["id"],
            rows[3]["id"],
        ]
        assert await resolve(query.count()) == 2
        empty = await resolve(
            scoped_query(search_module, table, marker).search("unfindablelexeme").execute()
        )
        assert empty == {"data": [], "total": 0}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_vector_ranking_paging_count_and_dimension_rejection(search_module, live_resources):
    async with search_rows(search_module, live_resources) as (table, marker, rows):
        query = (
            scoped_query(search_module, table, marker)
            .vector_search(
                "embedding", [1.0, 0.0, 0.0], topk=3, metric="cosine", threshold=0.5, ef_search=32
            )
            .page_size(1)
        )
        first = await resolve(query.execute())
        second = await resolve(query.page(2).execute())
        assert [row["id"] for row in first["data"]] == [rows[0]["id"]]
        assert [row["id"] for row in second["data"]] == [rows[1]["id"]]
        assert first["data"][0]["_vector_score"] == pytest.approx(0.0)
        assert first["data"][0]["_similarity_score"] == pytest.approx(1.0)
        assert second["data"][0]["_vector_score"] == pytest.approx(0.2)
        assert "embedding" not in first["data"][0]
        assert "embedding" not in second["data"][0]
        assert await resolve(query.count()) == 2
        with pytest.raises(ValidationError) as error:
            await resolve(
                scoped_query(search_module, table, marker)
                .vector_search("embedding", [1.0])
                .execute()
            )
        assert "dimension" in str(error.value).lower()
        assert await resolve(scoped_query(search_module, table, marker).count()) == 3


@pytest.mark.integration
@pytest.mark.asyncio
async def test_hybrid_extreme_weights_select_correct_candidates(search_module, live_resources):
    async with search_rows(search_module, live_resources) as (table, marker, rows):
        text_only = await resolve(
            scoped_query(search_module, table, marker)
            .vector_search("embedding", [1.0, 0.0, 0.0], topk=4)
            .search("invoice")
            .hybrid(alpha=0.0)
            .execute()
        )
        assert {row["id"] for row in text_only["data"]} == {rows[0]["id"], rows[3]["id"]}
        assert text_only["total"] == 2
        assert all(row["_fts_score"] > 0 for row in text_only["data"])
        vector_only = await resolve(
            scoped_query(search_module, table, marker)
            .vector_search("embedding", [1.0, 0.0, 0.0], topk=4)
            .search("invoice")
            .hybrid(alpha=1.0)
            .execute()
        )
        # alpha=1 skips the text leg. Every scoped non-NULL embedding is a
        # candidate, including an orthogonal vector: RRF scores use rank, not
        # raw cosine similarity, and no distance threshold was requested.
        assert [row["id"] for row in vector_only["data"]] == [
            rows[0]["id"],
            rows[1]["id"],
            rows[3]["id"],
        ]
        assert vector_only["total"] == 3
        assert all(row["_fts_score"] == 0 for row in vector_only["data"])
        assert all(row["_hybrid_score"] == row["_vector_score"] for row in vector_only["data"])
        scores = [row["_vector_score"] for row in vector_only["data"]]
        assert scores[0] > scores[1] > scores[2] > 0


def test_search_sets_param():
    """The plain full-text builder uses the search query parameter."""
    from types import SimpleNamespace

    from taruvi._sync.modules.database import _BaseQueryBuilder

    builder = _BaseQueryBuilder(None, SimpleNamespace(app_slug="test"), "documents")
    assert "search" not in builder.build_params()
    builder._set_search("hello world")
    assert builder.build_params()["search"] == "hello world"
