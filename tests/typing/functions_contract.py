"""Static contract probe; run mypy with imported module diagnostics silent."""

from taruvi._async.modules.functions import AsyncFunctionsModule
from taruvi._sync.modules.functions import FunctionsModule
from taruvi.types import FunctionInvocation

INVOCATION: FunctionInvocation = {
    "id": 42,
    "function": 17,
    "function_name": "count_items",
    "function_slug": "count-items",
    "celery_task_id": "task-42",
    "trigger_type": "api",
    "user_id": None,
    "user_username": None,
    "user_email": None,
    "task_result": {
        "task_id": "task-42",
        "status": "SUCCESS",
        "result": {"result": False, "success": True},
        "traceback": None,
        "task_args": {"dry_run": False},
        "task_kwargs": {},
        "task_name": "functions.execute",
        "date_created": "2026-10-03T12:00:00Z",
        "date_done": "2026-10-03T12:00:00Z",
        "worker": None,
        "meta": {},
    },
    "history_id": None,
    "logs": [
        {
            "timestamp": "2026-10-03T12:00:00+00:00",
            "level": "INFO",
            "logger": "stdout",
            "message": "completed",
        }
    ],
    "log_count": 1,
    "has_error": False,
    "created_at": "2026-10-03T12:00:00Z",
    "updated_at": "2026-10-03T12:00:00Z",
}


def check_functions(functions: FunctionsModule) -> None:
    execution = functions.execute("count-items", {"dry_run": False}, is_async=False)
    queued: bool | None = execution.get("queued")
    print(queued, execution["invocation"]["function"], execution["data"])
    record = functions.get_invocation("42")
    task = record["task_result"]
    if task is not None:
        status: str = task["status"]
        print(status, task["result"])


async def check_async_functions(functions: "AsyncFunctionsModule") -> None:
    execution = await functions.execute("count-items", {"dry_run": False}, is_async=True)
    queued: bool | None = execution.get("queued")
    print(queued, execution["invocation"]["function"], execution["data"])
    page = await functions.list_invocations(page=2, page_size=10)
    record: FunctionInvocation = page["data"][0]
    print(record["task_result"])
