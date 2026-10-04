"""
Type definitions for Taruvi SDK.

These are TypedDict definitions for IDE autocomplete and type checking.
Methods still return plain dicts - these are type hints only, NOT runtime validation.

Usage:
    from taruvi.types import User, DatabaseFilters

    def get(self, username: str) -> User:
        # Returns dict, but IDE knows the structure
        ...
"""

import sys
from typing import Any, Literal, TypedDict

if sys.version_info >= (3, 11):
    from typing import NotRequired
else:
    from typing_extensions import NotRequired


# ============================================================================
# Response Types - API Response Structures
# ============================================================================


class User(TypedDict):
    """Tenant user as serialized by the platform's user detail endpoint."""

    id: str  # UUID serialized as a string
    email: str
    username: str
    first_name: str
    last_name: str
    full_name: str
    is_active: bool
    is_cloud_user: bool
    is_superuser: bool
    is_deleted: bool
    date_joined: str
    last_login: str | None
    icon_url: str | None
    groups: NotRequired[list[dict[str, Any]]]
    user_permissions: NotRequired[list[dict[str, Any]]]
    roles: NotRequired[list[dict[str, Any]]]
    attributes: NotRequired[dict[str, Any]]
    missing_attributes: NotRequired[dict[str, Any] | list[dict[str, Any]]]


class UserResponse(TypedDict):
    """Single-user response envelope retained by users.get/create/update."""

    status: Literal["success"]
    message: str
    data: User


class DatabaseRecord(TypedDict, total=False):
    """Generic database record (type hint only).

    Use total=False to allow any additional fields.
    """

    id: int | str
    created_at: str
    updated_at: str
    # Additional fields allowed via total=False


class PgRangeValue(TypedDict):
    """PostgreSQL range column value as returned by the API."""

    lower: str | int | float | None
    upper: str | int | float | None
    bounds: Literal["()", "(]", "[)", "[]"]
    empty: bool


class StorageFile(TypedDict):
    """Storage file metadata (type hint only)."""

    id: str
    filename: str
    path: str
    size: int
    mimetype: str
    storage_provider: Literal["s3", "sharepoint"]
    is_office_editable: bool
    visibility: Literal["public", "private"]
    created_at: str
    url: NotRequired[str]
    metadata: NotRequired[dict[str, Any]]


class StorageAccessLinkResult(TypedDict):
    """Result of a SharePoint view or edit access grant."""

    url: str
    mode: Literal["view", "edit"]


class StorageBrowseFolder(TypedDict):
    """Virtual folder entry from browse (type hint only)."""

    type: Literal["folder"]
    name: str
    path: str  # e.g. "reports/2024/" — pass back as prefix to browse deeper


class StorageBrowseFile(TypedDict):
    """File entry from browse (type hint only)."""

    type: Literal["file"]
    id: int
    uuid: str
    name: str
    path: str
    size: int
    mimetype: str
    visibility: str
    is_office_editable: bool
    created_at: str
    updated_at: str
    download_url: NotRequired[str | None]


class StorageBrowseData(TypedDict):
    """Response payload from browse (type hint only)."""

    prefix: str
    folders: list["StorageBrowseFolder"]
    objects: list["StorageBrowseFile"]
    has_next: bool
    page: int
    page_size: int


class Function(TypedDict):
    """Function definition (type hint only)."""

    id: int
    name: str
    slug: str
    environment: Literal["python", "javascript"]
    execution_mode: Literal["app", "proxy", "system"]
    app: NotRequired[int | None]
    app_name: NotRequired[str | None]
    app_slug: NotRequired[str | None]
    is_active: bool
    async_mode: bool
    created_at: str | None
    updated_at: str | None


class FunctionTaskResult(TypedDict):
    """Celery result data; global lookup omits fields present on invocation metadata."""

    task_id: str
    status: str
    result: Any
    date_created: str | None
    date_done: str | None
    traceback: NotRequired[str | None]
    task_args: NotRequired[Any]
    task_kwargs: NotRequired[Any]
    task_name: NotRequired[str | None]
    worker: NotRequired[str | None]
    meta: NotRequired[Any]


class FunctionInvocation(TypedDict):
    """Invocation serializer record. Task state lives in nullable task_result."""

    id: int
    function: int
    function_name: str
    function_slug: str
    celery_task_id: str
    trigger_type: str
    user_id: str | None
    user_username: str | None
    user_email: str | None
    task_result: FunctionTaskResult | None
    history_id: int | None
    logs: NotRequired[list[dict[str, Any]] | None]
    log_count: int
    has_error: bool
    created_at: str | None
    updated_at: str | None
    executed_code: NotRequired[str | None]


class FunctionExecutionResponse(TypedDict):
    """Full execute envelope, with queued optional for older platform releases."""

    status: Literal["success", "error"]
    message: str
    data: Any
    invocation: FunctionInvocation
    queued: NotRequired[bool]
    success: NotRequired[bool]


class FunctionInvocationListResponse(TypedDict):
    """Page-number invocation listing; list records omit heavy logs."""

    status: Literal["success", "error"]
    message: str
    data: list[FunctionInvocation]
    total: int


class FunctionListResponse(TypedDict):
    """Limit/offset function listing."""

    status: Literal["success", "error"]
    message: str
    data: list[Function]
    total: int


class FunctionTaskResultResponse(TypedDict):
    """Global task lookup envelope; result remains the executor's stored output."""

    status: Literal["success", "error"]
    message: str
    data: FunctionTaskResult


class Secret(TypedDict):
    """A secret (type hint only). ``get()`` returns ``value``; list responses omit it."""

    key: str
    value: NotRequired[str | dict[str, Any]]
    tags: NotRequired[list[str]]
    name: NotRequired[str]
    description: NotRequired[str]
    secret_type: NotRequired[str]
    created_at: str
    updated_at: str


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
    """One Cerbos resource result from the platform's check/resources endpoint."""

    resource: dict[str, str]
    actions: dict[str, str]
    validation_errors: NotRequired[list[dict[str, Any]]]
    outputs: NotRequired[list[dict[str, Any]]]
    meta: NotRequired[dict[str, Any]]


class PolicyCheckBatchResult(TypedDict):
    """Batch resource/action check response (without a data envelope)."""

    results: list[PolicyCheckResult]
    request_id: NotRequired[str]
    cerbos_call_id: NotRequired[str]


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
    environment: Literal["python", "javascript"]


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
    is_superuser: bool
    is_deleted: bool
    is_cloud_user: bool
    roles: str  # Comma-separated
    ordering: str
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

__all__ = [  # noqa: RUF022 - grouped by kind on purpose
    # Response types
    "User",
    "UserResponse",
    "DatabaseRecord",
    "StorageFile",
    "StorageAccessLinkResult",
    "StorageBrowseFolder",
    "StorageBrowseFile",
    "StorageBrowseData",
    "Function",
    "FunctionInvocation",
    "FunctionExecutionResponse",
    "FunctionInvocationListResponse",
    "FunctionListResponse",
    "FunctionTaskResult",
    "FunctionTaskResultResponse",
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
