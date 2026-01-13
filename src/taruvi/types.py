"""
Type definitions for Taruvi SDK.

These are TypedDict definitions for IDE autocomplete and type checking.
Methods still return plain dicts - these are type hints only, NOT runtime validation.

Usage:
    from taruvi.types import User, DatabaseFilters

    def get_user(self, username: str) -> User:
        # Returns dict, but IDE knows the structure
        ...
"""

from typing import TypedDict, Literal, Any, Optional
try:
    from typing import NotRequired  # Python 3.11+
except ImportError:
    from typing_extensions import NotRequired  # Python 3.8-3.10

from datetime import datetime


# ============================================================================
# Response Types - API Response Structures
# ============================================================================

class User(TypedDict):
    """User response structure (type hint only)."""
    id: str
    email: str
    username: str
    first_name: NotRequired[str]
    last_name: NotRequired[str]
    is_active: bool
    is_staff: bool
    created_at: str  # ISO datetime string
    updated_at: str


class DatabaseRecord(TypedDict, total=False):
    """Generic database record (type hint only).

    Use total=False to allow any additional fields.
    """
    id: int | str
    created_at: str
    updated_at: str
    # Additional fields allowed via total=False


class StorageFile(TypedDict):
    """Storage file metadata (type hint only)."""
    id: str
    filename: str
    path: str
    size: int
    mimetype: str
    visibility: Literal["public", "private"]
    created_at: str
    url: NotRequired[str]
    metadata: NotRequired[dict[str, Any]]


class Function(TypedDict):
    """Function definition (type hint only)."""
    id: int
    name: str
    slug: str
    environment: Literal["python", "node"]
    execution_mode: Literal["app", "system"]
    app: NotRequired[int]
    app_name: NotRequired[str]
    app_slug: NotRequired[str]
    is_active: bool
    async_mode: bool
    created_at: str
    updated_at: str


class FunctionInvocation(TypedDict):
    """Function invocation result (type hint only)."""
    id: int
    celery_task_id: NotRequired[str]
    status: Literal["pending", "PENDING", "running", "STARTED", "completed", "SUCCESS", "FAILURE"]
    result: NotRequired[Any]
    error: NotRequired[str]


class Secret(TypedDict):
    """Secret metadata (type hint only)."""
    key: str
    name: NotRequired[str]
    description: NotRequired[str]
    secret_type: NotRequired[str]
    created_at: str
    updated_at: str
    # value is NOT included in list responses (security)


class Bucket(TypedDict):
    """Storage bucket metadata (type hint only)."""
    id: int
    name: str
    slug: str
    visibility: Literal["public", "private"]
    file_size_limit: NotRequired[int]
    allowed_mime_types: NotRequired[list[str]]
    file_count: NotRequired[int]
    total_size: NotRequired[int]
    created_at: str
    updated_at: str


class App(TypedDict):
    """App metadata (type hint only)."""
    id: int
    name: str
    slug: str
    description: NotRequired[str]
    is_active: bool
    created_at: str
    updated_at: str


class Setting(TypedDict):
    """App setting (type hint only)."""
    key: str
    value: Any
    description: NotRequired[str]
    setting_type: NotRequired[str]
    created_at: str
    updated_at: str


class PolicyCheckResult(TypedDict):
    """Policy check result (type hint only)."""
    allowed: bool
    resource: str
    action: str
    principal: str
    metadata: NotRequired[dict[str, Any]]


class PolicyCheckBatchResult(TypedDict):
    """Batch policy check result (type hint only)."""
    results: list[PolicyCheckResult]


class AnalyticsQueryResult(TypedDict):
    """Analytics query result (type hint only)."""
    data: Any  # Query-specific result structure (varies by query)


# ============================================================================
# Filter Types - Query Parameters
# ============================================================================

class DatabaseFilters(TypedDict, total=False):
    """Database query filters (type hint only)."""
    page: int
    page_size: int
    ordering: str
    # Django-style field filters (e.g., age__gte=18)
    # Can't define all possibilities, so allow any additional fields


class StorageFilters(TypedDict, total=False):
    """Storage query filters (type hint only)."""
    page: int
    page_size: int
    search: str
    mimetype: str
    visibility: Literal["public", "private"]
    ordering: str


class FunctionFilters(TypedDict, total=False):
    """Function list filters (type hint only)."""
    limit: int
    offset: int
    is_active: bool
    environment: Literal["python", "node"]


class SecretFilters(TypedDict, total=False):
    """Secret list filters (type hint only)."""
    search: str
    app: str
    tags: str  # Comma-separated
    secret_type: str
    page: int
    page_size: int


class UserFilters(TypedDict, total=False):
    """User list filters (type hint only)."""
    search: str
    is_active: bool
    is_staff: bool
    roles: str  # Comma-separated
    page: int
    page_size: int


# ============================================================================
# Paginated Response
# ============================================================================

class PaginatedResponse(TypedDict):
    """Paginated API response (type hint only)."""
    count: int
    next: NotRequired[str]
    previous: NotRequired[str]
    results: list[Any]


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Response types
    "User",
    "DatabaseRecord",
    "StorageFile",
    "Function",
    "FunctionInvocation",
    "Secret",
    "Bucket",
    "App",
    "Setting",
    "PolicyCheckResult",
    "PolicyCheckBatchResult",
    "AnalyticsQueryResult",
    "PaginatedResponse",

    # Filter types
    "DatabaseFilters",
    "StorageFilters",
    "FunctionFilters",
    "SecretFilters",
    "UserFilters",
]
