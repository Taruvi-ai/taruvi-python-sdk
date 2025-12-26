"""
Functions API Module

Provides methods for:
- Executing functions
- Listing functions
- Getting function details
- Managing function invocations
"""

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from taruvi.client import Client


class FunctionsModule:
    """Functions API operations."""

    def __init__(self, client: "Client") -> None:
        """
        Initialize Functions module.

        Args:
            client: Taruvi client instance
        """
        self.client = client
        self._http = client._http_client
        self._config = client._config

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
            params: Function parameters (passed to function's `params` argument)
            app_slug: App slug (defaults to client's app_slug)
            is_async: Whether to execute asynchronously (returns task_id)
            timeout: Override default timeout for this request

        Returns:
            dict: Function execution result
                - If sync: {"success": bool, "data": Any, "message": str}
                - If async: {"task_id": str, "status": str}

        Raises:
            NotFoundError: If function not found
            ValidationError: If parameters are invalid
            FunctionExecutionError: If function execution fails

        Example:
            ```python
            # Synchronous execution
            result = await client.functions.execute(
                "process-order",
                params={"order_id": 123, "action": "ship"}
            )
            print(result["data"])

            # Asynchronous execution
            task = await client.functions.execute(
                "long-running-job",
                params={"batch_size": 1000},
                is_async=True
            )
            print(f"Task ID: {task['task_id']}")
            ```
        """
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required (provide via parameter or Client config)")

        # Build request path
        path = f"/api/apps/{app_slug}/functions/{function_slug}/execute/"

        # Build request body
        body = {
            "params": params or {},
            "async": is_async,
        }

        # Execute request
        headers = {}
        if timeout:
            # Note: httpx doesn't support per-request timeout via headers,
            # but we can pass it to the request method
            pass

        response = await self._http.post(path, json=body, headers=headers)
        return response

    async def list(
        self,
        *,
        app_slug: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        List functions in an app.

        Args:
            app_slug: App slug (defaults to client's app_slug)
            limit: Maximum number of functions to return
            offset: Offset for pagination

        Returns:
            dict: List of functions with pagination info

        Example:
            ```python
            functions = await client.functions.list()
            for func in functions["data"]:
                print(f"{func['name']}: {func['slug']}")
            ```
        """
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = f"/api/apps/{app_slug}/functions/"
        params = {"limit": limit, "offset": offset}

        response = await self._http.get(path, params=params)
        return response

    async def get(
        self,
        function_slug: str,
        *,
        app_slug: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get function details.

        Args:
            function_slug: Function slug
            app_slug: App slug (defaults to client's app_slug)

        Returns:
            dict: Function details

        Example:
            ```python
            func = await client.functions.get("my-function")
            print(f"Name: {func['name']}")
            print(f"Mode: {func['execution_mode']}")
            ```
        """
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = f"/api/apps/{app_slug}/functions/{function_slug}/"
        response = await self._http.get(path)
        return response

    async def get_invocation(
        self,
        invocation_id: str,
        *,
        app_slug: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get function invocation details.

        Args:
            invocation_id: Invocation ID or task ID
            app_slug: App slug (defaults to client's app_slug)

        Returns:
            dict: Invocation details including status, result, logs

        Example:
            ```python
            invocation = await client.functions.get_invocation("task_123")
            print(f"Status: {invocation['status']}")
            print(f"Result: {invocation['result']}")
            ```
        """
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = f"/api/apps/{app_slug}/invocations/{invocation_id}/"
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
        """
        List function invocations.

        Args:
            function_slug: Filter by function slug
            app_slug: App slug (defaults to client's app_slug)
            status: Filter by status (pending, running, completed, failed)
            limit: Maximum number of invocations to return
            offset: Offset for pagination

        Returns:
            dict: List of invocations with pagination info

        Example:
            ```python
            invocations = await client.functions.list_invocations(
                function_slug="my-function",
                status="completed"
            )
            for inv in invocations["data"]:
                print(f"{inv['id']}: {inv['status']}")
            ```
        """
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = f"/api/apps/{app_slug}/invocations/"
        params: dict[str, Any] = {"limit": limit, "offset": offset}

        if function_slug:
            params["function_slug"] = function_slug
        if status:
            params["status"] = status

        response = await self._http.get(path, params=params)
        return response
