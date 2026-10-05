"""Function and policy contracts through the actual SDK request loop and HTTPX transport.

Fixtures were generated with FunctionInvocationRecordSerializer and AppDataResponse
from the platform checkout. The policy fixture uses its Cerbos protobuf and
MessageToDict with preserving_proto_field_name=True. No live services are touched.
"""

import json
from pathlib import Path

import httpx
import pytest

from taruvi._async.client import AsyncClient
from taruvi._sync.client import SyncClient

WIRE = json.loads((Path(__file__).parent / "fixtures/function-wire.json").read_text())
POLICY_WIRE = json.loads((Path(__file__).parent / "fixtures/policy-wire.json").read_text())
BASE = "https://api.example.com/sites/demo"


def sync_client(handler):
    client = SyncClient(BASE, "app", api_key="fixture", max_retries=0)
    client._http_client.client.close()
    client._http_client.client = httpx.Client(base_url=BASE, transport=httpx.MockTransport(handler))
    return client


async def async_client(handler):
    client = AsyncClient(BASE, "app", api_key="fixture", max_retries=0)
    await client._http_client.client.aclose()
    client._http_client.client = httpx.AsyncClient(
        base_url=BASE, transport=httpx.MockTransport(handler)
    )
    return client


@pytest.mark.parametrize("queued", [False, True])
def test_sync_functions_preserve_execute_envelope_and_mode(unauth_test_config, queued):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(202 if queued else 200, json=WIRE["queued" if queued else "sync"])

    client = sync_client(handler)
    try:
        response = client.functions.execute("count-items", {"dry_run": False}, is_async=queued)
    finally:
        client.close()
    assert response == WIRE["queued" if queued else "sync"]
    assert response["queued"] is queued
    assert response["invocation"]["task_result"]["status"] == "SUCCESS"
    assert response["invocation"]["user_username"] is None
    assert requests[0].url.path == "/sites/demo/api/apps/app/functions/count-items/execute/"
    assert json.loads(requests[0].content) == {"params": {"dry_run": False}, "async": queued}


@pytest.mark.asyncio
@pytest.mark.parametrize("queued", [False, True])
async def test_async_functions_preserve_execute_envelope_and_mode(unauth_test_config, queued):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(202 if queued else 200, json=WIRE["queued" if queued else "sync"])

    client = await async_client(handler)
    try:
        response = await client.functions.execute(
            "count-items", {"dry_run": False}, is_async=queued
        )
    finally:
        await client.close()
    assert response == WIRE["queued" if queued else "sync"]
    assert response["queued"] is queued
    assert requests[0].url.path == "/sites/demo/api/apps/app/functions/count-items/execute/"
    assert json.loads(requests[0].content)["async"] is queued


def test_invocation_detail_and_list_have_distinct_envelopes_and_canonical_paging(
    unauth_test_config,
):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(
            200, json=WIRE["detail" if request.url.path.endswith("/42/") else "invocations"]
        )

    client = sync_client(handler)
    try:
        detail = client.functions.get_invocation(42)
        page = client.functions.list_invocations(
            page=2, page_size=10, function_slug="count-items", has_error=False
        )
    finally:
        client.close()
    assert detail == WIRE["detail"]
    assert page == WIRE["invocations"]
    assert "logs" in detail and "logs" not in page["data"][0]
    assert requests[0].url.path == "/sites/demo/api/invocations/42/"
    assert dict(requests[1].url.params) == {
        "page": "2",
        "page_size": "10",
        "function_slug": "count-items",
        "has_error": "false",
    }


@pytest.mark.asyncio
async def test_async_invocation_detail_list_and_result_envelopes(unauth_test_config):
    def handler(request):
        key = (
            "task_response"
            if "/result/" in request.url.path
            else "invocations" if request.url.path.endswith("/invocations/") else "detail"
        )
        return httpx.Response(200, json=WIRE[key])

    client = await async_client(handler)
    try:
        detail = await client.functions.get_invocation(42)
        result = await client.functions.get_result("task-42")
        page = await client.functions.list_invocations(
            page=2, page_size=10, function_slug="count-items"
        )
    finally:
        await client.close()
    assert detail["function"] == 17
    assert detail["task_result"]["task_args"] == {"dry_run": False}
    assert result == WIRE["task_response"]
    assert result["data"]["status"] == "SUCCESS"
    assert page == WIRE["invocations"]


def test_legacy_invocation_paging_maps_only_aligned_offsets_and_rejects_unsupported_status(
    unauth_test_config,
):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=WIRE["invocations"])

    client = sync_client(handler)
    try:
        client.functions.list_invocations(limit=10, offset=20)
        with pytest.raises(ValueError, match="multiple"):
            client.functions.list_invocations(limit=10, offset=3)
        with pytest.raises(ValueError, match="status"):
            client.functions.list_invocations(status="SUCCESS")
    finally:
        client.close()
    assert len(requests) == 1
    assert dict(requests[0].url.params) == {"page": "3", "page_size": "10"}


def test_sync_policy_preserves_protobuf_metadata(unauth_test_config):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=POLICY_WIRE)

    client = sync_client(handler)
    resources = [{"resource": {"id": "row-1", "kind": "datatable"}, "actions": ["read"]}]
    try:
        response = client.policy.check_resources(resources)
    finally:
        client.close()
    assert response == POLICY_WIRE
    assert response["request_id"] == "typing-probe"
    assert response["cerbos_call_id"] == "call-probe"
    resource = response["results"][0]
    assert resource["resource"]["policy_version"] == "default"
    assert resource["actions"]["read"] == "EFFECT_ALLOW"
    assert resource["validation_errors"] == [{"path": "attr.owner", "message": "owner is required"}]
    assert requests[0].method == "POST"
    assert requests[0].url.path == "/sites/demo/api/apps/app/check/resources/"
    assert json.loads(requests[0].content) == {"resources": resources}


@pytest.mark.asyncio
async def test_async_policy_preserves_protobuf_metadata(unauth_test_config):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=POLICY_WIRE)

    client = await async_client(handler)
    resources = [{"resource": {"id": "row-1", "kind": "datatable"}, "actions": ["read"]}]
    try:
        response = await client.policy.check_resources(resources)
    finally:
        await client.close()
    assert response == POLICY_WIRE
    assert response["request_id"] == "typing-probe"
    assert response["cerbos_call_id"] == "call-probe"
    resource = response["results"][0]
    assert resource["resource"]["policy_version"] == "default"
    assert resource["actions"]["read"] == "EFFECT_ALLOW"
    assert resource["validation_errors"] == [{"path": "attr.owner", "message": "owner is required"}]
    assert requests[0].method == "POST"
    assert requests[0].url.path == "/sites/demo/api/apps/app/check/resources/"
    assert json.loads(requests[0].content) == {"resources": resources}
