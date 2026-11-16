"""Typed filters survive the SDK's real JSON and URL transports."""

import json
from contextlib import asynccontextmanager
from datetime import date, datetime
from uuid import UUID

import httpx
import pytest

from taruvi import Client


@asynccontextmanager
async def recording_client(mode):
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(200, json={"data": [], "total": 0})

    client = Client(api_url="https://sdk.test", app_slug="app", api_key="fixture-key", mode=mode)
    http = client._http_client
    if mode == "async":
        await http.client.aclose()
        http.client = httpx.AsyncClient(
            base_url="https://sdk.test", transport=httpx.MockTransport(respond)
        )
    else:
        http.client.close()
        http.client = httpx.Client(
            base_url="https://sdk.test", transport=httpx.MockTransport(respond)
        )
    try:
        yield client, requests
    finally:
        if mode == "async":
            await http.client.aclose()
        else:
            http.client.close()


async def execute(query, mode):
    return await query.execute() if mode == "async" else query.execute()


@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize(
    ("operator", "value", "expected"),
    [
        ("between", [1, 3], {"value__between": [1, 3]}),
        ("between", (1, 3), {"value__between": [1, 3]}),
        ("in", [1, 3], {"value__in": [1, 3]}),
        ("in", [], {"value__in": []}),
        ("in", [None, False, "007", 7], {"value__in": [None, False, "007", 7]}),
        ("rcontains", [1, 3], {"value__rcontains": [1, 3]}),
        ("acontains", ["a,b", "c"], {"value__acontains": ["a,b", "c"]}),
    ],
)
async def test_vector_filter_lists_stay_json_arrays(mode, operator, value, expected):
    async with recording_client(mode) as (client, requests):
        query = client.database.from_("items").filter("value", operator, value)
        await execute(query.vector_search("embedding", [0.1]), mode)

    assert requests[0].method == "POST"
    assert requests[0].url.query == b""
    assert json.loads(requests[0].content)["filters"] == expected


@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (UUID("12345678-1234-4234-8234-123456789012"), "12345678-1234-4234-8234-123456789012"),
        (date(2026, 1, 2), "2026-01-02"),
        (datetime(2026, 1, 2, 3, 4, 5), "2026-01-02T03:04:05"),
        (datetime.fromisoformat("2026-01-02T03:04:05+00:00"), "2026-01-02T03:04:05Z"),
        (
            datetime.fromisoformat("2026-01-02T03:04:05+05:30"),
            "2026-01-02T03:04:05+05:30",
        ),
        (False, False),
        (None, None),
        ([], []),
        (1, 1),
        (1.5, 1.5),
        ("007", "007"),
    ],
)
async def test_vector_filter_scalars_have_json_representations(mode, value, expected):
    async with recording_client(mode) as (client, requests):
        query = client.database.from_("items").filter("value", "eq", value)
        await execute(query.vector_search("embedding", [0.1]), mode)

    actual = json.loads(requests[0].content)["filters"]["value"]
    assert actual == expected
    assert type(actual) is type(expected)


@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize("vector", [False, True])
async def test_nested_filter_trees_serialize_uuid_and_datetime(mode, vector):
    filters = {
        "or": [
            {"owner_id": UUID("12345678-1234-4234-8234-123456789012")},
            {"created_at__gte": datetime.fromisoformat("2026-01-02T00:00:00+00:00")},
        ]
    }
    async with recording_client(mode) as (client, requests):
        query = client.database.from_("items").filter(filters)
        if vector:
            query.vector_search("embedding", [0.1])
        await execute(query, mode)

    filters = (
        json.loads(requests[0].content)["filters"]
        if vector
        else json.loads(requests[0].url.params["filters"])
    )
    assert filters == {
        "or": [
            {"owner_id": "12345678-1234-4234-8234-123456789012"},
            {"created_at__gte": "2026-01-02T00:00:00Z"},
        ]
    }


@pytest.mark.parametrize("mode", ["sync", "async"])
async def test_typed_simple_filters_combine_with_refine_filters(mode):
    async with recording_client(mode) as (client, requests):
        query = client.database.from_("items").filter("id", "between", [1, 3])
        query.filter([{"field": "created_at", "operator": "gte", "value": date(2026, 1, 2)}])
        await execute(query.vector_search("embedding", [0.1]), mode)

    assert json.loads(requests[0].content)["filters"] == {
        "and": [{"id__between": [1, 3]}, {"created_at__gte": "2026-01-02"}]
    }


@pytest.mark.parametrize("mode", ["sync", "async"])
async def test_repeated_list_filters_remain_separate_conditions(mode):
    async with recording_client(mode) as (client, requests):
        query = client.database.from_("items").filter("id", "in", [1, 2]).filter("id", "in", [2, 3])
        await execute(query.vector_search("embedding", [0.1]), mode)

    assert json.loads(requests[0].content)["filters"] == {
        "and": [{"id__in": [1, 2]}, {"id__in": [2, 3]}]
    }


@pytest.mark.parametrize("mode", ["sync", "async"])
async def test_filter_captures_list_before_the_caller_mutates_it(mode):
    values = [1, 3]
    async with recording_client(mode) as (client, requests):
        query = client.database.from_("items").filter("id", "between", values)
        values.append(5)
        await execute(query.vector_search("embedding", [0.1]), mode)

    assert json.loads(requests[0].content)["filters"] == {"id__between": [1, 3]}


@pytest.mark.parametrize("mode", ["sync", "async"])
async def test_get_and_filtered_delete_keep_legacy_list_encoding(mode):
    async with recording_client(mode) as (client, requests):
        query = client.database.from_("items").filter("id", "between", [1, 3])
        await execute(query, mode)
        await execute(query.delete_filtered(), mode)

    assert requests[0].method == "GET"
    assert requests[0].url.params["id__between"] == "1,3"
    assert requests[1].method == "DELETE"
    assert json.loads(requests[1].url.params["filter"]) == {"id__between": "1,3"}


@pytest.mark.parametrize("mode", ["sync", "async"])
async def test_get_keeps_legacy_repeated_list_encoding(mode):
    async with recording_client(mode) as (client, requests):
        query = client.database.from_("items").filter("id", "in", [1, 2]).filter("id", "in", [2, 3])
        await execute(query, mode)

    assert requests[0].url.params.get_list("id__in") == ["1,2", "2,3"]
