"""
Synchronous HTTP Client with Retry Logic

Native blocking HTTP client using httpx.Client (no asyncio wrappers).
Handles all HTTP communication with Taruvi API, including:
- Automatic retries with exponential backoff
- Connection pooling
- Timeout handling
- Error response parsing
"""

import logging
import time
from typing import Any, Optional

import httpx

from taruvi.config import TaruviConfig
from taruvi.exceptions import (
    ConnectionError,
    NetworkError,
    NotAuthenticatedError,
    ResponseError,
    TimeoutError,
    create_error_from_response,
)

logger = logging.getLogger(__name__)


class SyncHTTPClient:
    """
    Synchronous HTTP client for Taruvi API with retry logic.

    Uses native httpx.Client (blocking) - NO asyncio.run() wrapper.
    Thread-safe and works in any Python environment including
    Jupyter notebooks, FastAPI apps, and async contexts.

    Features:
    - Automatic retries with exponential backoff
    - Connection pooling for performance
    - Comprehensive error handling
    - Request/response logging
    """

    def __init__(self, config: TaruviConfig) -> None:
        """
        Initialize synchronous HTTP client.

        Args:
            config: Taruvi configuration
        """
        self.config = config

        # Create httpx client with connection pooling (use defaults)
        limits = httpx.Limits(
            max_connections=10,
            max_keepalive_connections=10,
        )

        self.client = httpx.Client(
            base_url=config.api_url,
            timeout=config.timeout,
            limits=limits,
            verify=True,  # Always verify SSL
            follow_redirects=True,
        )

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
        Make an HTTP request with retry logic (blocking).

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

                # Handle response
                return self._handle_response(response)

            except httpx.TimeoutException as e:
                if attempt >= max_retries:
                    raise TimeoutError(
                        f"Request timed out after {self.config.timeout}s",
                        details={"path": path, "method": method},
                    ) from e

                # Wait before retry (simple backoff: 1s, 2s, 4s...)
                wait_time = 2**attempt
                time.sleep(wait_time)

            except (httpx.ConnectError, httpx.NetworkError) as e:
                if attempt >= max_retries:
                    raise ConnectionError(
                        f"Failed to connect to {self.config.api_url}",
                        details={"path": path, "method": method, "error": str(e)},
                    ) from e

                # Wait before retry (simple backoff: 1s, 2s, 4s...)
                wait_time = 2**attempt
                time.sleep(wait_time)

            except Exception as e:
                # Don't retry on unexpected errors
                raise NetworkError(
                    f"Unexpected network error: {str(e)}",
                    details={"path": path, "method": method},
                ) from e

        # Should never reach here, but satisfy type checker
        raise NetworkError("Max retries exceeded")

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
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
        # Check for errors
        if response.status_code >= 400:
            self._handle_error_response(response)

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

    def _is_client_authenticated(self) -> bool:
        """
        Check if client has authentication credentials configured.

        Returns:
            True if client has jwt, api_key, or session_token
        """
        return any([
            self.config.jwt is not None,
            self.config.api_key is not None,
            self.config.session_token is not None,
        ])

    def _handle_error_response(self, response: httpx.Response) -> None:
        """
        Handle error response and raise appropriate exception.

        Args:
            response: httpx Response object

        Raises:
            APIError: Appropriate error based on status code
            NotAuthenticatedError: When accessing protected resource without authentication
        """
        # Special handling for 401 when client is not authenticated
        if response.status_code == 401 and not self._is_client_authenticated():
            raise NotAuthenticatedError(
                "Authentication required for this resource. "
                "Use client.auth.signInWithToken() or client.auth.signInWithPassword() to authenticate."
            )

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

        raise error

    # Convenience methods
    def get(
        self,
        path: str,
        *,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Make a GET request (blocking)."""
        return self.request("GET", path, params=params, headers=headers)

    def post(
        self,
        path: str,
        *,
        json: Optional[dict[str, Any]] = None,
        data: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Make a POST request (blocking)."""
        return self.request("POST", path, json=json, data=data, headers=headers)

    def put(
        self,
        path: str,
        *,
        json: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Make a PUT request (blocking)."""
        return self.request("PUT", path, json=json, headers=headers)

    def patch(
        self,
        path: str,
        *,
        json: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Make a PATCH request (blocking)."""
        return self.request("PATCH", path, json=json, headers=headers)

    def delete(
        self,
        path: str,
        *,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Make a DELETE request (blocking)."""
        return self.request("DELETE", path, params=params, headers=headers)

    def __enter__(self):
        """Support context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close client on context exit."""
        self.close()
