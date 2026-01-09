"""
Base HTTP Client with Shared Logic

Provides shared functionality for both async and sync HTTP clients:
- Response handling
- Error handling
- Authentication checking
- JSON parsing
"""

import logging
from typing import Any, Optional

import httpx

from taruvi.config import TaruviConfig
from taruvi.exceptions import (
    NotAuthenticatedError,
    ResponseError,
    create_error_from_response,
)

logger = logging.getLogger(__name__)


class BaseHTTPClient:
    """
    Base HTTP client with shared logic for async and sync implementations.

    Provides:
    - Response handling and JSON parsing
    - Error response handling
    - Authentication checking
    - Header management
    """

    def __init__(self, config: TaruviConfig) -> None:
        """
        Initialize base HTTP client.

        Args:
            config: Taruvi configuration
        """
        self.config = config

    def _create_client_limits(self) -> httpx.Limits:
        """Create connection pool limits (shared configuration)."""
        return httpx.Limits(
            max_connections=10,
            max_keepalive_connections=10,
        )

    def _create_client_kwargs(self) -> dict[str, Any]:
        """Create common httpx client kwargs."""
        return {
            "base_url": self.config.api_url,
            "timeout": self.config.timeout,
            "limits": self._create_client_limits(),
            "verify": True,  # Always verify SSL
            "follow_redirects": True,
        }

    def _merge_headers(self, additional_headers: Optional[dict[str, str]] = None) -> dict[str, str]:
        """
        Merge default headers with additional headers.

        Args:
            additional_headers: Optional headers to merge

        Returns:
            Merged headers dict
        """
        headers = self.config.headers.copy()
        if additional_headers:
            headers.update(additional_headers)
        return headers

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

    def _parse_json_response(self, response: httpx.Response) -> dict[str, Any]:
        """
        Parse JSON from response.

        Args:
            response: httpx Response object

        Returns:
            Parsed JSON dict

        Raises:
            ResponseError: If JSON parsing fails
        """
        try:
            return response.json()
        except Exception as e:
            raise ResponseError(
                "Failed to parse JSON response",
                details={
                    "status_code": response.status_code,
                    "content": response.text[:500],  # First 500 chars
                },
            ) from e

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

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """
        Handle HTTP response - check for errors and parse JSON.

        Args:
            response: httpx Response object

        Returns:
            Parsed JSON response

        Raises:
            APIError: For error status codes
            ResponseError: For invalid JSON
        """
        # Check for errors
        if response.status_code >= 400:
            self._handle_error_response(response)

        # Parse and return JSON
        return self._parse_json_response(response)
