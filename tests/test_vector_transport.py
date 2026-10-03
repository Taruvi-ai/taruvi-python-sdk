"""Public sync/async vector builders through the real HTTP client boundary.

The transport captures actual httpx requests and supplies wire responses.
Ranking, indexes and authorization require separate platform integration tests.
"""

import inspect
import json
from types import SimpleNamespace

import httpx
import pytest

from taruvi import Client, NotFoundError, ValidationError


async def resolve(value):
    return await value if inspect.isawaitable(value) else value


@pytest.fixture(params=["sync", "async"])
async def transport_client(request, monkeypatch):
    monkeypatch.setenv("TARUVI_TEST_MODE", "true")
    client = Client(
        api_url="https://tenant.example.com/sites/vector-fixture",
        app_slug="search-app",
        mode=request.param,
        api_key="fixture-key",
        max_retries=0,
    )
    await resolve(client.close())
    boundary = SimpleNamespace(
        client=client, requests=[], status=200, response={"data": [], "total": 0}
    )

    def handle(message):
        boundary.requests.append(message)
        return httpx.Response(boundary.status, json=boundary.response)

    transport_type = httpx.AsyncClient if request.param == "async" else httpx.Client
    client._http_client.client = transport_type(
        base_url=client.config.api_url,
        transport=httpx.MockTransport(handle),
        trust_env=False,
    )
    try:
        yield boundary
    finally:
        await resolve(client.close())


@pytest.mark.asyncio
async def test_vector_defaults_keep_the_site_path_and_preserve_scores(transport_client):
    boundary = transport_client
    rows = [{"id": 4, "_vector_score": 0.2, "_similarity_score": 0.8}]
    boundary.response = {"status": "success", "data": rows, "total": 1}
    result = await resolve(
        boundary.client.database.from_("documents")
        .vector_search("embedding", [0.1, -0.2, 0])
        .execute()
    )
    assert result == {"data": rows, "total": 1}
    request = boundary.requests[0]
    assert request.method == "POST"
    assert (
        request.url.path
        == "/sites/vector-fixture/api/apps/search-app/datatables/documents/data/query/"
    )
    assert request.headers["Authorization"] == "Api-Key fixture-key"
    assert json.loads(request.content) == {
        "vector": {"field": "embedding", "value": [0.1, -0.2, 0], "topk": 10}
    }


@pytest.mark.asyncio
async def test_vector_controls_coexist_with_scalar_tree_and_page_filters(transport_client):
    boundary = transport_client
    filters = {"or": [{"visibility": "public"}, {"owner_id": 7}]}
    query = (
        boundary.client.database.from_("documents")
        .vector_search("embedding", [1.0, 0.0], topk=50, metric="ip", threshold=0.0, ef_search=64)
        .filter("category", "in", ["guide", "faq"])
        .filter(filters)
        .sort("id")
        .page_size(5)
        .page(2)
    )
    assert await resolve(query.execute()) == {"data": [], "total": 0}
    assert json.loads(boundary.requests[0].content) == {
        "filters": {"and": [{"category__in": ["guide", "faq"]}, filters]},
        "ordering": ["id"],
        "page_size": 5,
        "page": 2,
        "vector": {
            "field": "embedding",
            "value": [1.0, 0.0],
            "topk": 50,
            "metric": "ip",
            "threshold": 0.0,
            "ef_search": 64,
        },
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("alpha", [0.0, 1.0])
async def test_hybrid_preserves_zero_and_one_weights_and_search_text(transport_client, alpha):
    boundary = transport_client
    boundary.response = {
        "data": [{"id": 3, "_hybrid_score": 0.04, "_vector_score": 0.02, "_fts_score": 0.06}],
        "total": 1,
    }
    result = await resolve(
        boundary.client.database.from_("documents")
        .vector_search("embedding", [1, 0], topk=8)
        .search("invoice + paid? 世界")
        .hybrid(strategy="rrf", alpha=alpha)
        .execute()
    )
    assert json.loads(boundary.requests[0].content) == {
        "search": "invoice + paid? 世界",
        "vector": {"field": "embedding", "value": [1, 0], "topk": 8},
        "hybrid": {"strategy": "rrf", "alpha": alpha},
    }
    assert result == boundary.response


@pytest.mark.asyncio
async def test_scalar_reads_still_use_get(transport_client):
    boundary = transport_client
    await resolve(
        boundary.client.database.from_("documents").filter("active", "eq", True).execute()
    )
    request = boundary.requests[0]
    assert request.method == "GET"
    assert (
        request.url.path == "/sites/vector-fixture/api/apps/search-app/datatables/documents/data/"
    )
    assert dict(request.url.params) == {"active": "true"}


@pytest.mark.asyncio
async def test_backend_vector_validation_error_is_not_converted_to_an_empty_result(
    transport_client,
):
    boundary = transport_client
    boundary.status = 400
    boundary.response = {
        "status": "error",
        "code": "VALIDATION_ERROR",
        "message": "Vector dimensions do not match",
    }
    with pytest.raises(ValidationError, match="Vector dimensions do not match"):
        await resolve(
            boundary.client.database.from_("documents").vector_search("embedding", [1]).execute()
        )
    assert len(boundary.requests) == 1


@pytest.mark.asyncio
async def test_vector_narrowing_cannot_be_silently_dropped_from_a_delete(transport_client):
    query = (
        transport_client.client.database.from_("documents")
        .filter("active", "eq", True)
        .vector_search("embedding", [1, 0])
    )
    with pytest.raises(ValueError, match="can't narrow a delete by vector_search"):
        await resolve(query.delete_filtered().execute())
    assert transport_client.requests == []


@pytest.mark.asyncio
async def test_vector_combines_overlapping_filters_without_overwriting(transport_client):
    query = (
        transport_client.client.database.from_("documents")
        .filter("category", "eq", "public")
        .filter("score", "gt", 1)
        .filter("score", "gt", 5)
        .filter({"category": "private"})
        .vector_search("embedding", [1, 0])
    )
    await resolve(query.execute())
    assert json.loads(transport_client.requests[0].content)["filters"] == {
        "and": [{"category": "public"}, {"score__gt": 1}, {"score__gt": 5}, {"category": "private"}]
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("with_raw_list", [False, True])
async def test_vector_filters_preserve_typed_list_values(transport_client, with_raw_list):
    values = ["a,b", "007", True, 4]
    query = transport_client.client.database.from_("documents").filter("tag", "in", values)
    if with_raw_list:
        query.filter([{"field": "active", "operator": "eq", "value": False}])
    await resolve(query.vector_search("embedding", [1, 0]).execute())
    filters = json.loads(transport_client.requests[0].content)["filters"]
    expected = (
        [
            {"field": "tag", "operator": "in", "value": values},
            {"field": "active", "operator": "eq", "value": False},
        ]
        if with_raw_list
        else {"tag__in": values}
    )
    assert filters == expected
    actual_values = filters[0]["value"] if with_raw_list else filters["tag__in"]
    assert [type(value) for value in actual_values] == [str, str, bool, int]


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["execute", "count"])
async def test_single_record_vector_query_is_rejected_before_transport(transport_client, operation):
    query = (
        transport_client.client.database.from_("documents")
        .get(7)
        .vector_search("embedding", [1, 0])
    )
    with pytest.raises(ValueError, match="vector_search.*get"):
        await resolve(getattr(query, operation)())
    assert transport_client.requests == []


@pytest.mark.asyncio
async def test_large_vector_count_uses_post_without_mutating_the_requested_page(transport_client):
    boundary = transport_client
    boundary.response = {"data": [{"id": 1}], "total": 9}
    vector = [0.123456789] * 1536
    query = (
        boundary.client.database.from_("documents")
        .filter("category", "eq", "public")
        .vector_search("embedding", vector, topk=10, metric="cosine", threshold=0.4, ef_search=32)
        .search("machine learning")
        .hybrid(alpha=0.0)
        .sort("id")
        .page(2)
        .page_size(3)
    )
    assert await resolve(query.count()) == 9
    request = boundary.requests[0]
    assert request.method == "POST"
    assert request.url.path.endswith("/data/query/")
    assert not request.url.query
    body = json.loads(request.content)
    assert body == {
        "filters": {"category": "public"},
        "search": "machine learning",
        "ordering": ["id"],
        "vector": {
            "field": "embedding",
            "value": vector,
            "topk": 10,
            "metric": "cosine",
            "threshold": 0.4,
            "ef_search": 32,
        },
        "hybrid": {"strategy": "rrf", "alpha": 0.0},
    }
    await resolve(query.execute())
    later_body = json.loads(boundary.requests[1].content)
    assert (later_body["page"], later_body["page_size"]) == (2, 3)


@pytest.mark.asyncio
async def test_scalar_list_filters_and_single_record_path_remain_get(transport_client):
    query = (
        transport_client.client.database.from_("documents")
        .get(7)
        .filter("tag", "in", ["guide", "faq"])
    )
    await resolve(query.execute())
    request = transport_client.requests[0]
    assert request.method == "GET"
    assert request.url.path.endswith("/data/7/")
    assert dict(request.url.params) == {"tag__in": "guide,faq"}


@pytest.mark.asyncio
async def test_backend_without_query_route_returns_not_found_without_get_fallback(transport_client):
    transport_client.status = 404
    transport_client.response = {"message": "Not found"}
    query = transport_client.client.database.from_("documents").vector_search("embedding", [1, 0])
    with pytest.raises(NotFoundError):
        await resolve(query.execute())
    assert [(request.method, request.url.path) for request in transport_client.requests] == [
        ("POST", "/sites/vector-fixture/api/apps/search-app/datatables/documents/data/query/")
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["get", "update", "delete"])
async def test_record_identity_cannot_become_a_query_or_fragment(transport_client, operation):
    from urllib.parse import quote

    identity = "a?secret=b#fragment/percent%value"
    query = transport_client.client.database.from_("documents")
    if operation == "delete":
        query = query.delete(identity)
    else:
        query = query.get(identity)
        if operation == "update":
            query = query.update({"title": "edited"})
    await resolve(query.execute())
    request = transport_client.requests[0]
    assert request.method == {"get": "GET", "update": "PATCH", "delete": "DELETE"}[operation]
    assert (
        request.url.raw_path
        == (
            "/sites/vector-fixture/api/apps/search-app/datatables/documents/data/"
            + quote(identity, safe="")
            + "/"
        ).encode()
    )
    assert not request.url.query
    assert not request.url.fragment
