"""
Functions API Module

Provides methods for:
- Executing functions (async)
- Getting function execution results by task ID
- Listing functions
- Getting function details
- Managing function invocations
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from taruvi.modules.base import BaseModule

if TYPE_CHECKING:
    from taruvi._async.client import AsyncClient

# API endpoint paths for functions
_FUNCTIONS_BASE = "/api/apps/{app_slug}/functions/"
_FUNCTION_DETAIL = "/api/apps/{app_slug}/functions/{function_slug}/"
_FUNCTION_EXECUTE = "/api/apps/{app_slug}/functions/{function_slug}/execute/"
_FUNCTION_RESULT = "/api/result/{task_id}/"
_INVOCATIONS_LIST = "/api/apps/{app_slug}/invocations/"
_INVOCATION_DETAIL = "/api/apps/{app_slug}/invocations/{invocation_id}/"


# ============================================================================
# Shared Implementation Logic
# ============================================================================

def _build_execute_request(
    params: Optional[dict[str, Any]],
    is_async: bool
) -> dict[str, Any]:
    """Build function execution request body."""
    return {
        "params": params or {},
        "async": is_async,
    }


def _build_list_params(limit: int, offset: int) -> dict[str, int]:
    """Build list request params."""
    return {"limit": limit, "offset": offset}


def _build_invocations_params(
    function_slug: Optional[str],
    status: Optional[str],
    limit: int,
    offset: int
) -> dict[str, Any]:
    """Build invocations list params."""
    params: dict[str, Any] = {"limit": limit, "offset": offset}

    if function_slug:
        params["function_slug"] = function_slug
    if status:
        params["status"] = status

    return params


class AsyncFunctionsModule(BaseModule):
    """Functions API operations."""

    def __init__(self, client: "AsyncClient") -> None:
        """Initialize FunctionsModule."""
        self.client = client
        super().__init__(client._http_client, client._config)

    async def execute(
        self,
        function_slug: str,
        params: Optional[dict[str, Any]] = None,
        *,
        app_slug: Optional[str] = None,
        is_async: bool = False,
        timeout: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Execute a function.

        Args:
            function_slug: Function slug (e.g., "my-function")
            params: Function parameters
            app_slug: App slug (defaults to client's app_slug)
            is_async: Whether to execute asynchronously (returns task_id)
            timeout: Override default timeout

        Returns:
            FunctionExecutionResult: Function execution result

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

        path = _FUNCTION_EXECUTE.format(
            app_slug=app_slug,
            function_slug=function_slug
        )
        body = _build_execute_request(params, is_async)

        response = await self._http.post(path, json=body, headers={})
        return response

    async def get_result(
        self,
        task_id: str,
    ) -> dict[str, Any]:
        """
        Get the result of a function execution by task ID.

        Args:
            task_id: Celery task ID returned from async execution

        Returns:
            Dict containing:
                - task_id: The task identifier
                - status: Task status (SUCCESS, FAILURE, PENDING, etc.)
                - result: Task result data (if completed successfully)
                - traceback: Error traceback (if failed)
                - date_created: Task creation timestamp
                - date_done: Task completion timestamp
                - params: User-provided execution parameters

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
            print(task_result['status'])  # 'SUCCESS', 'FAILURE', etc.
            print(task_result['result'])  # Actual function output
            ```
        """
        path = _FUNCTION_RESULT.format(task_id=task_id)
        response = await self._http.get(path)
        return response

    async def list(
        self,
        *,
        app_slug: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List functions in an app."""
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _FUNCTIONS_BASE.format(app_slug=app_slug)
        params = _build_list_params(limit, offset)

        response = await self._http.get(path, params=params)
        return response

    async def get(
        self,
        function_slug: str,
        *,
        app_slug: Optional[str] = None,
    ) -> dict[str, Any]:
        """Get function details."""
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _FUNCTION_DETAIL.format(app_slug=app_slug, function_slug=function_slug)
        response = await self._http.get(path)
        return response

    async def get_invocation(
        self,
        invocation_id: str,
        *,
        app_slug: Optional[str] = None,
    ) -> dict[str, Any]:
        """Get function invocation details."""
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _INVOCATION_DETAIL.format(app_slug=app_slug, invocation_id=invocation_id)
        response = await self._http.get(path)
        return response

    async def list_invocations(
        self,
        *,
        function_slug: Optional[str] = None,
        app_slug: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List function invocations."""
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _INVOCATIONS_LIST.format(app_slug=app_slug)
        params = _build_invocations_params(function_slug, status, limit, offset)

        response = await self._http.get(path, params=params)
        return response
