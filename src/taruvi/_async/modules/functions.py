"""
Functions API Module

Provides methods for:
- Executing functions synchronously or queueing asynchronous runs
- Getting function execution results by task ID
- Listing functions
- Getting function details
- Managing function invocations
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union, cast

from taruvi.modules.base import BaseModule
from taruvi.types import (
    Function,
    FunctionExecutionResponse,
    FunctionInvocation,
    FunctionInvocationListResponse,
    FunctionListResponse,
    FunctionTaskResultResponse,
)
from taruvi.utils import build_params

if TYPE_CHECKING:
    from taruvi._async.client import AsyncClient

# API endpoint paths for functions
_FUNCTIONS_BASE = "/api/apps/{app_slug}/functions/"
_FUNCTION_DETAIL = "/api/apps/{app_slug}/functions/{function_slug}/"
_FUNCTION_EXECUTE = "/api/apps/{app_slug}/functions/{function_slug}/execute/"
_FUNCTION_RESULT = "/api/result/{task_id}/"
_INVOCATIONS_LIST = "/api/invocations/"
_INVOCATION_DETAIL = "/api/invocations/{invocation_id}/"


# ============================================================================
# Shared Implementation Logic
# ============================================================================


def _build_execute_request(
    params: Optional[dict[str, Any]], is_async: Optional[bool]
) -> dict[str, Any]:
    """Build function execution request body.

    ``async`` is omitted when ``is_async`` is None so the function's own
    default execution mode applies.
    """
    body: dict[str, Any] = {"params": params or {}}
    if is_async is not None:
        body["async"] = is_async
    return body


def _build_invocation_params(
    *,
    function_slug: Optional[str],
    status: Optional[str],
    page: Optional[int],
    page_size: Optional[int],
    limit: Optional[int],
    offset: Optional[int],
    function_id: Optional[int],
    trigger_type: Optional[str],
    user_id: Optional[str],
    has_error: Optional[bool],
) -> dict[str, Any]:
    if status is not None:
        raise ValueError(
            "status filtering is not supported; inspect each invocation's task_result.status"
        )
    if page_size is not None and limit is not None:
        raise ValueError("Use page_size or its legacy limit alias, not both")
    if page is not None and offset is not None:
        raise ValueError("Use page or its legacy offset alias, not both")
    size = page_size if page_size is not None else limit if limit is not None else 100
    if size < 1:
        raise ValueError("page_size must be positive")
    if offset is not None and (offset < 0 or offset % size):
        raise ValueError("Legacy offset must be a nonnegative multiple of page_size/limit")
    current = page if page is not None else (offset // size + 1 if offset is not None else 1)
    if current < 1:
        raise ValueError("page must be positive")
    return build_params(
        function_slug=function_slug,
        function_id=function_id,
        trigger_type=trigger_type,
        user_id=user_id,
        has_error=has_error,
        page=current,
        page_size=size,
    )


class AsyncFunctionsModule(BaseModule):
    """Functions API operations."""

    def __init__(self, client: AsyncClient) -> None:
        """Initialize FunctionsModule."""
        self.client = client
        super().__init__(client._http_client, client._config)

    async def execute(
        self,
        function_slug: str,
        params: Optional[dict[str, Any]] = None,
        *,
        app_slug: Optional[str] = None,
        is_async: Optional[bool] = None,
        timeout: Optional[int] = None,
    ) -> FunctionExecutionResponse:
        """
        Execute a function.

        Args:
            function_slug: Function slug (e.g., "my-function")
            params: Function parameters
            app_slug: App slug (defaults to client's app_slug)
            is_async: True to queue the run and return a task ID, False to wait
                for the result. None (default) uses the function's own mode.
            timeout: Seconds to wait for this call, overriding the client's timeout

        Returns:
            Full FunctionExecutionResponse envelope: data, invocation, and optional queued flag

        Example:
            ```python
            result = await client.functions.execute(
                "process-order",
                params={"order_id": 123}
            )
            ```
        """
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _FUNCTION_EXECUTE.format(app_slug=app_slug, function_slug=function_slug)
        body = _build_execute_request(params, is_async)

        response = await self.client._http_client.post(path, json=body, headers={}, timeout=timeout)
        return cast(FunctionExecutionResponse, response)

    async def get_result(
        self,
        task_id: str,
    ) -> FunctionTaskResultResponse:
        """
        Get the result of a function execution by task ID.

        Args:
            task_id: Celery task ID returned from async execution

        Returns:
            Envelope whose data contains:
                - task_id: The task identifier
                - status: Task status (SUCCESS, FAILURE, PENDING, etc.)
                - result: Task result data (if completed successfully)
                - traceback: Error traceback (if failed)
                - date_created: Task creation timestamp
                - date_done: Task completion timestamp

        Example:
            ```python
            # Execute function asynchronously
            result = await client.functions.execute(
                "process-order",
                params={"order_id": 123},
                is_async=True
            )
            task_id = result['invocation']['celery_task_id']

            # Get result later
            task_result = await client.functions.get_result(task_id)
            print(task_result['data']['status'])  # 'SUCCESS', 'FAILURE', etc.
            print(task_result['data']['result'])  # Actual function output
            ```
        """
        path = _FUNCTION_RESULT.format(task_id=task_id)
        response = await self.client._http_client.get(path)
        return cast(FunctionTaskResultResponse, response)

    async def list(
        self,
        *,
        app_slug: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> FunctionListResponse:
        """List functions in an app."""
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _FUNCTIONS_BASE.format(app_slug=app_slug)
        params = build_params(limit=limit, offset=offset)

        response = await self.client._http_client.get(path, params=params)
        return cast(FunctionListResponse, response)

    async def get(
        self,
        function_slug: str,
        *,
        app_slug: Optional[str] = None,
    ) -> Function:
        """Get function details."""
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _FUNCTION_DETAIL.format(app_slug=app_slug, function_slug=function_slug)
        response = await self.client._http_client.get(path)
        return cast(Function, response)

    async def get_invocation(
        self,
        invocation_id: Union[int, str],
    ) -> FunctionInvocation:
        """Get function invocation details."""
        path = _INVOCATION_DETAIL.format(invocation_id=invocation_id)
        response = await self.client._http_client.get(path)
        return cast(FunctionInvocation, response)

    async def list_invocations(
        self,
        *,
        function_slug: Optional[str] = None,
        status: Optional[str] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        function_id: Optional[int] = None,
        trigger_type: Optional[str] = None,
        user_id: Optional[str] = None,
        has_error: Optional[bool] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> FunctionInvocationListResponse:
        """List invocation records using page/page_size.

        The backend supports function, trigger, user and has_error filters.
        It does not filter by Celery status; status is rejected instead of ignored.
        Legacy limit/offset map to a page only when offset is aligned to the size.
        Stay within the platform's configured maximum page size for exact paging.
        """
        params = _build_invocation_params(
            function_slug=function_slug,
            status=status,
            page=page,
            page_size=page_size,
            limit=limit,
            offset=offset,
            function_id=function_id,
            trigger_type=trigger_type,
            user_id=user_id,
            has_error=has_error,
        )
        response = await self.client._http_client.get(_INVOCATIONS_LIST, params=params)
        return cast(FunctionInvocationListResponse, response)
