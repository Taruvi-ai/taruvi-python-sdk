"""Real broker/worker Functions acceptance using the owned echo function.

A queued HTTP response is acceptance only. These cases wait for persisted
terminal task results and verify invocation identity and payload, through both
public clients. The fixture owner removes the function and its audit records.
"""

import asyncio
import inspect
import time
from uuid import uuid4

import pytest

from taruvi.exceptions import NotFoundError

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def resolve(value):
    return await value if inspect.isawaitable(value) else value


@pytest.fixture(params=["sync", "async"])
def functions_module(request, sync_functions_module, async_functions_module):
    return sync_functions_module if request.param == "sync" else async_functions_module


async def completed_task(module, task_id):
    deadline = time.monotonic() + 60
    while True:
        response = await resolve(module.get_result(task_id))
        assert response["status"] == "success"
        task = response["data"]
        assert task["task_id"] == task_id
        if task["status"] in {"SUCCESS", "FAILURE", "REVOKED"}:
            assert task["status"] == "SUCCESS", f"Owned task {task_id} finished {task['status']}"
            return task
        assert time.monotonic() < deadline, f"Owned task {task_id} remained {task['status']}"
        await asyncio.sleep(0.25)


@pytest.mark.parametrize("queued", [False, True])
async def test_execute_waits_for_actual_worker_result_and_invocation(
    functions_module, test_function_name, queued
):
    payload = {"marker": uuid4().hex, "value": False, "zero": 0, "empty": [], "nested": {"n": 7}}
    response = await resolve(functions_module.execute(test_function_name, payload, is_async=queued))
    assert response["status"] == "success"
    assert response["queued"] is queued
    invocation = response["invocation"]
    assert isinstance(invocation["id"], int)
    assert isinstance(invocation["function"], int)
    assert invocation["function_slug"] == test_function_name
    task_id = invocation["celery_task_id"]
    assert task_id
    assert response["data"] == ([] if queued else payload)

    task = await completed_task(functions_module, task_id)
    assert task["result"]["result"] == payload
    assert task["date_created"]
    assert task["date_done"]
    detail = await resolve(functions_module.get_invocation(invocation["id"]))
    assert detail["id"] == invocation["id"]
    assert detail["celery_task_id"] == task_id
    assert detail["task_result"]["status"] == "SUCCESS"
    assert detail["task_result"]["result"]["result"] == payload
    assert detail["has_error"] is False
    assert "logs" in detail

    page = await resolve(
        functions_module.list_invocations(function_slug=test_function_name, page=1, page_size=100)
    )
    assert page["total"] >= 1
    assert invocation["id"] in {record["id"] for record in page["data"]}
    assert all(record["function_slug"] == test_function_name for record in page["data"])
    assert all("logs" not in record for record in page["data"])


async def test_function_catalog_and_detail_agree(functions_module, test_function_name):
    page = await resolve(functions_module.list(limit=100, offset=0))
    assert page["status"] == "success"
    assert page["total"] >= 1
    catalog = next(item for item in page["data"] if item["slug"] == test_function_name)
    detail = await resolve(functions_module.get(test_function_name))
    assert detail["id"] == catalog["id"]
    assert detail["slug"] == test_function_name
    assert detail["execution_mode"] == "app"
    assert detail["is_active"] is True


async def test_unknown_function_is_not_found_but_unknown_task_is_pending(functions_module):
    with pytest.raises(NotFoundError):
        await resolve(functions_module.execute(f"absent-{uuid4().hex}", {}, is_async=False))
    task_id = str(uuid4())
    response = await resolve(functions_module.get_result(task_id))
    assert response["status"] == "success"
    assert response["data"]["task_id"] == task_id
    assert response["data"]["status"] == "PENDING"
    assert response["data"]["result"] is None
    assert response["data"]["date_done"] is None
