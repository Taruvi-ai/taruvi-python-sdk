"""Vector reads go in a POST body so the embedding is not put on the URL."""

from unittest.mock import AsyncMock, Mock

import pytest

from taruvi._async.modules.database import AsyncQueryBuilder
from taruvi._sync.modules.database import QueryBuilder


def _client(*, async_http: bool = False) -> Mock:
    client = Mock()
    client._http_client = AsyncMock() if async_http else Mock()
    client._config = Mock()
    client._config.app_slug = "policy-management"
    client._http_client.post.return_value = {"data": [{"id": 1}], "total": 1}
    client._http_client.get.return_value = {"data": [{"id": 2}], "total": 1}
    return client


def test_vector_search_posts_embedding_in_body():
    client = _client()
    result = (
        QueryBuilder(client, "document_chunks")
        .filter("document_id.category_id", "eq", "cat-1")
        .vector_search("embedding", [0.1, 0.2], topk=50)
        .execute()
    )

    client._http_client.get.assert_not_called()
    client._http_client.post.assert_called_once_with(
        "/api/apps/policy-management/datatables/document_chunks/data/query/",
        json={
            "vector": {"field": "embedding", "value": [0.1, 0.2], "topk": 50},
            "filters": {"document_id.category_id": "cat-1"},
        },
    )
    assert result == {"data": [{"id": 1}], "total": 1}


def test_vector_search_includes_optional_vector_fields():
    client = _client()
    (
        QueryBuilder(client, "document_chunks")
        .vector_search(
            "embedding",
            [0.1],
            topk=10,
            threshold=0.2,
            ef_search=80,
            metric="cosine",
        )
        .execute()
    )

    body = client._http_client.post.call_args.kwargs["json"]
    assert body["vector"] == {
        "field": "embedding",
        "value": [0.1],
        "topk": 10,
        "threshold": 0.2,
        "ef_search": 80,
        "metric": "cosine",
    }


def test_hybrid_without_search_stays_vector_only():
    client = _client()
    (
        QueryBuilder(client, "document_chunks")
        .vector_search("embedding", [0.1], topk=10)
        .hybrid(strategy="rrf", alpha=0.5)
        .execute()
    )

    body = client._http_client.post.call_args.kwargs["json"]
    assert "hybrid" not in body
    assert "search" not in body


def test_hybrid_with_search_is_sent():
    client = _client()
    (
        QueryBuilder(client, "document_chunks")
        .search("hi")
        .vector_search("embedding", [0.1], topk=10)
        .hybrid(strategy="rrf", alpha=0.5)
        .execute()
    )

    body = client._http_client.post.call_args.kwargs["json"]
    assert body["search"] == "hi"
    assert body["hybrid"] == {"strategy": "rrf", "alpha": 0.5}


def test_list_without_vector_stays_get():
    client = _client()
    QueryBuilder(client, "document_chunks").filter("status", "eq", "active").execute()

    client._http_client.post.assert_not_called()
    client._http_client.get.assert_called_once()
    assert client._http_client.get.call_args.args[0].endswith("/data/")


@pytest.mark.asyncio
async def test_async_vector_search_posts_embedding_in_body():
    client = _client(async_http=True)
    result = await (
        AsyncQueryBuilder(client, "document_chunks")
        .filter("document_id.category_id", "eq", "cat-1")
        .vector_search("embedding", [0.1, 0.2], topk=50)
        .execute()
    )

    client._http_client.get.assert_not_called()
    client._http_client.post.assert_called_once_with(
        "/api/apps/policy-management/datatables/document_chunks/data/query/",
        json={
            "vector": {"field": "embedding", "value": [0.1, 0.2], "topk": 50},
            "filters": {"document_id.category_id": "cat-1"},
        },
    )
    assert result == {"data": [{"id": 1}], "total": 1}
