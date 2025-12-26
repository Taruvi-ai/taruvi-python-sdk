"""
Taruvi SDK Exception Hierarchy

All exceptions inherit from TaruviError base class.
"""

from typing import Any, Optional


class TaruviError(Exception):
    """Base exception for all Taruvi SDK errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary representation."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details,
        }


# Configuration Errors
class ConfigurationError(TaruviError):
    """Raised when SDK configuration is invalid or missing."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, status_code=None, details=details)


# API Errors (mapped to HTTP status codes)
class APIError(TaruviError):
    """Base class for API-related errors."""

    pass


class ValidationError(APIError):
    """Raised when request validation fails (400 Bad Request)."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, status_code=400, details=details)


class AuthenticationError(APIError):
    """Raised when authentication fails (401 Unauthorized)."""

    def __init__(self, message: str = "Authentication failed", details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, status_code=401, details=details)


class AuthorizationError(APIError):
    """Raised when user lacks permission (403 Forbidden)."""

    def __init__(self, message: str = "Permission denied", details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, status_code=403, details=details)


class NotFoundError(APIError):
    """Raised when resource is not found (404 Not Found)."""

    def __init__(self, message: str = "Resource not found", details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, status_code=404, details=details)


class ConflictError(APIError):
    """Raised when there's a conflict (409 Conflict)."""

    def __init__(self, message: str = "Resource conflict", details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, status_code=409, details=details)


class RateLimitError(APIError):
    """Raised when rate limit is exceeded (429 Too Many Requests)."""

    def __init__(self, message: str = "Rate limit exceeded", details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, status_code=429, details=details)


class ServerError(APIError):
    """Raised when server encounters an error (500 Internal Server Error)."""

    def __init__(self, message: str = "Internal server error", details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, status_code=500, details=details)


class ServiceUnavailableError(APIError):
    """Raised when service is unavailable (503 Service Unavailable)."""

    def __init__(self, message: str = "Service temporarily unavailable", details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, status_code=503, details=details)


# Network Errors
class NetworkError(TaruviError):
    """Raised when network communication fails."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, status_code=None, details=details)


class TimeoutError(NetworkError):
    """Raised when request times out."""

    def __init__(self, message: str = "Request timed out", details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, details=details)


class ConnectionError(NetworkError):
    """Raised when connection to server fails."""

    def __init__(self, message: str = "Connection failed", details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, details=details)


# Runtime Errors
class RuntimeError(TaruviError):
    """Raised when there's an error during SDK runtime."""

    pass


class FunctionExecutionError(RuntimeError):
    """Raised when function execution fails."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, status_code=None, details=details)


# Response Parsing Errors
class ResponseError(TaruviError):
    """Raised when response cannot be parsed."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, status_code=None, details=details)


def create_error_from_response(status_code: int, message: str, details: Optional[dict[str, Any]] = None) -> APIError:
    """
    Create appropriate exception from HTTP response.

    Args:
        status_code: HTTP status code
        message: Error message
        details: Additional error details

    Returns:
        Appropriate APIError subclass
    """
    error_map: dict[int, type[APIError]] = {
        400: ValidationError,
        401: AuthenticationError,
        403: AuthorizationError,
        404: NotFoundError,
        409: ConflictError,
        429: RateLimitError,
        500: ServerError,
        503: ServiceUnavailableError,
    }

    error_class = error_map.get(status_code, APIError)
    return error_class(message, details)
