"""
Sync HTTP Client with Retry Logic

Handles all HTTP communication with Taruvi API using synchronous operations:
- Automatic retries with exponential backoff
- Connection pooling
- Timeout handling
- Error response parsing
"""

from __future__ import annotations

import logging
import sys
import time
from types import TracebackType
from typing import Any, Optional, Union

import httpx

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from taruvi.config import TaruviConfig
from taruvi.exceptions import (
    ConnectionError,
    NetworkError,
    TimeoutError,
)
from taruvi.http_client_base import BaseHTTPClient, can_retry

logger = logging.getLogger(__name__)


class HTTPClient(BaseHTTPClient):
    """
    Sync HTTP client for Taruvi API with retry logic.

    Inherits shared logic from BaseHTTPClient.

    Features:
    - Automatic retries with exponential backoff
    - Connection pooling for performance
    - Comprehensive error handling
    - Request/response logging
    """

    def __init__(self, config: TaruviConfig) -> None:
        """
        Initialize sync HTTP client.

        Args:
            config: Taruvi configuration
        """
        super().__init__(config)

        # Create sync httpx client with shared configuration
        self.client = httpx.Client(**self._create_client_kwargs())

    def close(self) -> None:
        """Close the HTTP client and release resources."""
        self.client.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict[str, Any]] = None,
        json: Optional[Union[dict[str, Any], list[dict[str, Any]]]] = None,
        data: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        retry: bool = True,
        timeout: Optional[float] = None,
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
            retry: Whether to retry on failure. POST and PATCH are only
                retried when the request never reached the server.
            timeout: Per-request timeout in seconds (defaults to the client's)

        Returns:
            dict: Parsed JSON response

        Raises:
            APIError: For API errors (4xx, 5xx)
            NetworkError: For network/connection errors
            TimeoutError: For request timeouts
            ResponseError: For response parsing errors
        """
        # Merge headers using base class method
        request_headers = self._merge_headers(headers)

        # Retry logic
        max_retries = self.config.max_retries if retry else 0

        for attempt in range(max_retries + 1):
            try:
                request_kwargs: dict[str, Any] = {}
                if timeout is not None:
                    request_kwargs["timeout"] = timeout
                response = self.client.request(
                    method=method,
                    url=path,
                    params=params,
                    json=json,
                    data=data,
                    headers=request_headers,
                    **request_kwargs,
                )

                # Handle response using base class method
                return self._handle_response(response)

            except httpx.TimeoutException as e:
                if attempt >= max_retries or not can_retry(method, e):
                    raise TimeoutError(
                        f"Request timed out after {timeout or self.config.timeout}s",
                        details={"path": path, "method": method},
                    ) from e

                # Wait before retry (exponential backoff: 1s, 2s, 4s...)
                wait_time = 2**attempt
                time.sleep(wait_time)

            except httpx.TransportError as e:
                if attempt >= max_retries or not can_retry(method, e):
                    raise ConnectionError(
                        f"Failed to connect to {self.config.api_url}",
                        details={"path": path, "method": method, "error": str(e)},
                    ) from e

                # Wait before retry (exponential backoff: 1s, 2s, 4s...)
                wait_time = 2**attempt
                time.sleep(wait_time)

        # Should never reach here, but satisfy type checker
        raise NetworkError("Max retries exceeded")

    # Convenience methods
    def get(
        self,
        path: str,
        *,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Make a GET request."""
        return self.request("GET", path, params=params, headers=headers)

    def post(
        self,
        path: str,
        *,
        params: Optional[dict[str, Any]] = None,
        json: Optional[Union[dict[str, Any], list[dict[str, Any]]]] = None,
        data: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> dict[str, Any]:
        """Make a POST request."""
        return self.request(
            "POST", path, params=params, json=json, data=data, headers=headers, timeout=timeout
        )

    def put(
        self,
        path: str,
        *,
        json: Optional[Union[dict[str, Any], list[dict[str, Any]]]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Make a PUT request."""
        return self.request("PUT", path, json=json, headers=headers)

    def patch(
        self,
        path: str,
        *,
        json: Optional[Union[dict[str, Any], list[dict[str, Any]]]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Make a PATCH request."""
        return self.request("PATCH", path, json=json, headers=headers)

    def delete(
        self,
        path: str,
        *,
        params: Optional[dict[str, Any]] = None,
        json: Optional[Union[dict[str, Any], list[dict[str, Any]]]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Make a DELETE request."""
        return self.request("DELETE", path, params=params, json=json, headers=headers)

    def __enter__(self) -> Self:
        """Support context manager."""
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Close client on context exit."""
        self.close()
