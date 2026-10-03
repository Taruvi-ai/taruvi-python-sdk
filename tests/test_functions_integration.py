"""Opt-in Functions acceptance against a disposable backend and existing function.

Run RUN_INTEGRATION_TESTS=1 pytest tests/test_functions_integration.py.
The default suite uses HTTPX contract fixtures and does not invoke live functions.
"""

import pytest

from taruvi.exceptions import TaruviError


def assert_execution(response, queued):
    assert response["status"] == "success"
    assert isinstance(response["invocation"]["id"], int)
    assert isinstance(response["invocation"]["function"], int)
    assert "task_result" in response["invocation"]
    if "queued" in response:  # older supported servers omit this additive flag
        assert response["queued"] is queued
    if queued:
        assert response["data"] == []
        assert response["invocation"]["celery_task_id"]


@pytest.mark.integration
@pytest.mark.parametrize("queued", [False, True])
def test_sync_execute_envelope(sync_functions_module, test_function_name, queued):
    response = sync_functions_module.execute(test_function_name, {"order_id": 123}, is_async=queued)
    assert_execution(response, queued)


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("queued", [False, True])
async def test_async_execute_envelope(async_functions_module, test_function_name, queued):
    response = await async_functions_module.execute(
        test_function_name, {"order_id": 123}, is_async=queued
    )
    assert_execution(response, queued)


@pytest.mark.integration
def test_sync_task_lookup_envelope(sync_functions_module, test_function_name):
    execution = sync_functions_module.execute(test_function_name, {"order_id": 456}, is_async=True)
    task_id = execution["invocation"]["celery_task_id"]
    result = sync_functions_module.get_result(task_id)
    assert result["data"]["task_id"] == task_id
    assert isinstance(result["data"]["status"], str)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_async_function_list_and_detail(async_functions_module, test_function_name):
    page = await async_functions_module.list(limit=10, offset=0)
    assert isinstance(page["data"], list)
    assert isinstance(page["total"], int)
    detail = await async_functions_module.get(test_function_name)
    assert detail["slug"] == test_function_name


@pytest.mark.integration
@pytest.mark.asyncio
async def test_missing_task_lookup_is_pending(async_functions_module):
    result = await async_functions_module.get_result("invalid-task-id-xyz")
    assert result["data"]["status"] == "PENDING"
    assert result["data"]["result"] is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_missing_function_is_refused(async_functions_module):
    with pytest.raises(TaruviError):
        await async_functions_module.execute("nonexistent-function-xyz-123", {}, is_async=False)
