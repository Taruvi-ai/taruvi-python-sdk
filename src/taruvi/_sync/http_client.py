"""
Sync HTTP Client with Retry Logic

Handles all HTTP communication with Taruvi API using synchronous operations:
- Automatic retries with exponential backoff
- Connection pooling
- Timeout handling
- Error response parsing
"""

import time
import logging
from typing import Any, Optional

import httpx

from taruvi.config import TaruviConfig
from taruvi.exceptions import (
    ConnectionError,
    NetworkError,
    TimeoutError,
)
from taruvi.http_client_base import BaseHTTPClient

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
        # Merge headers using base class method
        request_headers = self._merge_headers(headers)

        # Retry logic
        max_retries = self.config.max_retries if retry else 0

        for attempt in range(max_retries + 1):
            try:
                response = self.client.request(
                    method=method,
                    url=path,
                    params=params,
                    json=json,
                    data=data,
                    headers=request_headers,
                )

                # Handle response using base class method
                return self._handle_response(response)

            except httpx.TimeoutException as e:
                if attempt >= max_retries:
                    raise TimeoutError(
                        f"Request timed out after {self.config.timeout}s",
                        details={"path": path, "method": method},
                    ) from e

                # Wait before retry (exponential backoff: 1s, 2s, 4s...)
                wait_time = 2**attempt
                time.sleep(wait_time)

            except (httpx.ConnectError, httpx.NetworkError) as e:
                if attempt >= max_retries:
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
        json: Optional[dict[str, Any]] = None,
        data: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Make a POST request."""
        return self.request("POST", path, json=json, data=data, headers=headers)

    def put(
        self,
        path: str,
        *,
        json: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Make a PUT request."""
        return self.request("PUT", path, json=json, headers=headers)

    def patch(
        self,
        path: str,
        *,
        json: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Make a PATCH request."""
        return self.request("PATCH", path, json=json, headers=headers)

    def delete(
        self,
        path: str,
        *,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Make a DELETE request."""
        return self.request("DELETE", path, params=params, headers=headers)

    def __enter__(self):
        """Support context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close client on context exit."""
        self.close()
