"""
HTTP Client with Retry Logic

Handles all HTTP communication with Taruvi API, including:
- Automatic retries with exponential backoff
- Connection pooling
- Timeout handling
- Error response parsing
"""

import asyncio
import logging
from typing import Any, Optional

import httpx

from taruvi.config import TaruviConfig
from taruvi.exceptions import (
    ConnectionError,
    NetworkError,
    ResponseError,
    TimeoutError,
    create_error_from_response,
)

logger = logging.getLogger(__name__)


class HTTPClient:
    """
    Async HTTP client for Taruvi API with retry logic.

    Features:
    - Automatic retries with exponential backoff
    - Connection pooling for performance
    - Comprehensive error handling
    - Request/response logging
    """

    def __init__(self, config: TaruviConfig) -> None:
        """
        Initialize HTTP client.

        Args:
            config: Taruvi configuration
        """
        self.config = config

        # Create httpx client with connection pooling (use defaults)
        limits = httpx.Limits(
            max_connections=10,
            max_keepalive_connections=10,
        )

        self.client = httpx.AsyncClient(
            base_url=config.api_url,
            timeout=config.timeout,
            limits=limits,
            verify=True,  # Always verify SSL
            follow_redirects=True,
        )

    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        await self.client.aclose()

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict[str, Any]] = None,
        json: Optional[dict[str, Any]] = None,
        data: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        retry: bool = True,
    ) -> dict[str, Any]:
        """
        Make an HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            path: API endpoint path (e.g., "/api/apps")
            params: Query parameters
            json: JSON request body
            data: Form data
            headers: Additional headers (merged with default headers)
            retry: Whether to retry on failure

        Returns:
            dict: Parsed JSON response

        Raises:
            APIError: For API errors (4xx, 5xx)
            NetworkError: For network/connection errors
            TimeoutError: For request timeouts
            ResponseError: For response parsing errors
        """
        # Merge headers
        request_headers = self.config.headers.copy()
        if headers:
            request_headers.update(headers)

        # Retry logic
        max_retries = self.config.max_retries if retry else 0
        backoff_factor = self.config.retry_backoff_factor

        for attempt in range(max_retries + 1):
            try:
                if self.config.debug:
                    logger.debug(
                        f"Request: {method} {path} "
                        f"(attempt {attempt + 1}/{max_retries + 1})"
                    )

                response = await self.client.request(
                    method=method,
                    url=path,
                    params=params,
                    json=json,
                    data=data,
                    headers=request_headers,
                )

                # Handle response
                return await self._handle_response(response)

            except httpx.TimeoutException as e:
                if attempt >= max_retries:
                    raise TimeoutError(
                        f"Request timed out after {self.config.timeout}s",
                        details={"path": path, "method": method},
                    ) from e

                # Wait with exponential backoff
                wait_time = backoff_factor * (2**attempt)
                if self.config.debug:
                    logger.debug(f"Timeout, retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)

            except (httpx.ConnectError, httpx.NetworkError) as e:
                if attempt >= max_retries:
                    raise ConnectionError(
                        f"Failed to connect to {self.config.api_url}",
                        details={"path": path, "method": method, "error": str(e)},
                    ) from e

                # Wait with exponential backoff
                wait_time = backoff_factor * (2**attempt)
                if self.config.debug:
                    logger.debug(f"Connection error, retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)

            except Exception as e:
                # Don't retry on unexpected errors
                raise NetworkError(
                    f"Unexpected network error: {str(e)}",
                    details={"path": path, "method": method},
                ) from e

        # Should never reach here, but satisfy type checker
        raise NetworkError("Max retries exceeded")

    async def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """
        Handle HTTP response and parse JSON.

        Args:
            response: httpx Response object

        Returns:
            dict: Parsed JSON response

        Raises:
            APIError: For error status codes
            ResponseError: For invalid JSON
        """
        # Log response in debug mode
        if self.config.debug:
            logger.debug(f"Response: {response.status_code} {response.url}")

        # Check for errors
        if response.status_code >= 400:
            await self._handle_error_response(response)

        # Parse JSON
        try:
            data = response.json()
            return data
        except Exception as e:
            raise ResponseError(
                "Failed to parse JSON response",
                details={
                    "status_code": response.status_code,
                    "content": response.text[:500],  # First 500 chars
                },
            ) from e

    async def _handle_error_response(self, response: httpx.Response) -> None:
        """
        Handle error response and raise appropriate exception.

        Args:
            response: httpx Response object

        Raises:
            APIError: Appropriate error based on status code
        """
        # Try to parse error details from response
        try:
            error_data = response.json()
            message = error_data.get("message", response.text)
            details = error_data.get("details") or error_data.get("errors")
        except Exception:
            message = response.text or f"HTTP {response.status_code}"
            details = None

        # Create and raise appropriate error
        error = create_error_from_response(
            status_code=response.status_code,
            message=message,
            details=details,
        )

        if self.config.debug:
            logger.error(
                f"API Error: {response.status_code} - {message}",
                extra={"details": details},
            )

        raise error

    # Convenience methods
    async def get(
        self,
        path: str,
        *,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Make a GET request."""
        return await self.request("GET", path, params=params, headers=headers)

    async def post(
        self,
        path: str,
        *,
        json: Optional[dict[str, Any]] = None,
        data: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Make a POST request."""
        return await self.request("POST", path, json=json, data=data, headers=headers)

    async def put(
        self,
        path: str,
        *,
        json: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Make a PUT request."""
        return await self.request("PUT", path, json=json, headers=headers)

    async def patch(
        self,
        path: str,
        *,
        json: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Make a PATCH request."""
        return await self.request("PATCH", path, json=json, headers=headers)

    async def delete(
        self,
        path: str,
        *,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Make a DELETE request."""
        return await self.request("DELETE", path, params=params, headers=headers)

    async def __aenter__(self):
        """Support async context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close client on context exit."""
        await self.close()
