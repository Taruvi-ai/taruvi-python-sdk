"""
Taruvi SDK Exception Hierarchy

All exceptions inherit from TaruviError base class.
"""

from typing import Any, Optional


class TaruviError(Exception):
    """Base exception for all Taruvi SDK errors.

    API errors also carry the platform's error envelope: ``code`` is the
    standard error code (for example ``"NOT_FOUND"``) and ``detail`` is the
    optional human-readable context. Both are ``None`` when the response did
    not include them.
    """

    code: Optional[str] = None
    detail: Optional[str] = None

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
            "code": self.code,
            "detail": self.detail,
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


class ValidationError(APIError):
    """Raised when request validation fails (400 Bad Request)."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, status_code=400, details=details)


class AuthenticationError(APIError):
    """Raised when authentication fails (401 Unauthorized)."""

    def __init__(
        self, message: str = "Authentication failed", details: Optional[dict[str, Any]] = None
    ) -> None:
        super().__init__(message, status_code=401, details=details)


class NotAuthenticatedError(AuthenticationError):
    """Raised when attempting to access protected resource without authentication.

    A subclass of AuthenticationError, so ``except AuthenticationError`` also
    catches a 401 from a client that has no credential.
    """

    def __init__(
        self,
        message: str = "Authentication required for this resource",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details=details)


class AuthorizationError(APIError):
    """Raised when user lacks permission (403 Forbidden)."""

    def __init__(
        self, message: str = "Permission denied", details: Optional[dict[str, Any]] = None
    ) -> None:
        super().__init__(message, status_code=403, details=details)


class NotFoundError(APIError):
    """Raised when resource is not found (404 Not Found)."""

    def __init__(
        self, message: str = "Resource not found", details: Optional[dict[str, Any]] = None
    ) -> None:
        super().__init__(message, status_code=404, details=details)


class ConflictError(APIError):
    """Raised when there's a conflict (409 Conflict)."""

    def __init__(
        self, message: str = "Resource conflict", details: Optional[dict[str, Any]] = None
    ) -> None:
        super().__init__(message, status_code=409, details=details)


class RateLimitError(APIError):
    """Raised when rate limit is exceeded (429 Too Many Requests)."""

    def __init__(
        self, message: str = "Rate limit exceeded", details: Optional[dict[str, Any]] = None
    ) -> None:
        super().__init__(message, status_code=429, details=details)


class ServerError(APIError):
    """Raised when server encounters an error (500 Internal Server Error)."""

    def __init__(
        self, message: str = "Internal server error", details: Optional[dict[str, Any]] = None
    ) -> None:
        super().__init__(message, status_code=500, details=details)


class ServiceUnavailableError(APIError):
    """Raised when service is unavailable (503 Service Unavailable)."""

    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, status_code=503, details=details)


class BillingError(APIError):
    """The organization's billing blocked the request.

    ``code`` is ``"account_suspended"`` (402, the account isn't active),
    ``"product_suspended"`` (429, the plan's usage for ``module`` is used up for
    this period), or ``"gate_unavailable"`` (503, billing status couldn't be
    read; retry shortly).
    """

    def __init__(
        self,
        message: str,
        status_code: int,
        code: str,
        module: Optional[str] = None,
    ) -> None:
        super().__init__(message, status_code=status_code)
        self.code = code
        self.module = module
        self.retryable = code == "gate_unavailable"


BILLING_ERROR_CODES = frozenset({"account_suspended", "product_suspended", "gate_unavailable"})


class GatewayTimeoutError(APIError):
    """Raised when the platform times out a query or upstream call (504 Gateway Timeout)."""

    def __init__(
        self, message: str = "Gateway timeout", details: Optional[dict[str, Any]] = None
    ) -> None:
        super().__init__(message, status_code=504, details=details)


# Network Errors
class NetworkError(TaruviError):
    """Raised when network communication fails."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, status_code=None, details=details)


class TimeoutError(NetworkError):
    """Raised when request times out."""

    def __init__(
        self, message: str = "Request timed out", details: Optional[dict[str, Any]] = None
    ) -> None:
        super().__init__(message, details=details)


class ConnectionError(NetworkError):
    """Raised when connection to server fails."""

    def __init__(
        self, message: str = "Connection failed", details: Optional[dict[str, Any]] = None
    ) -> None:
        super().__init__(message, details=details)


# Runtime Errors
class RuntimeError(TaruviError):
    """Raised when there's an error during SDK runtime."""


class FunctionExecutionError(RuntimeError):
    """Raised when function execution fails."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, status_code=None, details=details)


# Response Parsing Errors
class ResponseError(TaruviError):
    """Raised when response cannot be parsed."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, status_code=None, details=details)


def create_error_from_response(
    status_code: int,
    message: str,
    details: Optional[dict[str, Any]] = None,
    code: Optional[str] = None,
    detail: Optional[str] = None,
    module: Optional[str] = None,
) -> APIError:
    """
    Create appropriate exception from HTTP response.

    Args:
        status_code: HTTP status code
        message: Error message
        details: Additional error details
        code: Standard error code from the response envelope
        detail: Human-readable context from the response envelope
        module: Product area blocked by a billing refusal

    Returns:
        Appropriate APIError subclass
    """
    if code in BILLING_ERROR_CODES:
        error = BillingError(message, status_code, code, module)
        error.detail = detail
        return error

    error_map: dict[int, type[APIError]] = {
        400: ValidationError,
        401: AuthenticationError,
        403: AuthorizationError,
        404: NotFoundError,
        409: ConflictError,
        429: RateLimitError,
        500: ServerError,
        503: ServiceUnavailableError,
        504: GatewayTimeoutError,
    }

    error_class = error_map.get(status_code)
    error = (
        error_class(message, details)
        if error_class is not None
        else APIError(message, status_code=status_code, details=details)
    )
    error.code = code
    error.detail = detail
    return error
