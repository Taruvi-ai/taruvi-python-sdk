"""
Shared utility functions for Taruvi SDK.

These utilities are used internally across SDK modules to:
- Build consistent query strings
- Construct URL paths safely
- Parse nested API responses
- Merge configuration dictionaries
"""

from typing import Any, Optional
from urllib.parse import urlencode


def build_query_string(
    params: Optional[dict[str, Any]],
    *,
    skip_none: bool = True,
    skip_empty: bool = True
) -> str:
    """
    Build URL query string from parameters.

    Args:
        params: Dictionary of query parameters
        skip_none: Skip None values (default: True)
        skip_empty: Skip empty strings (default: True)

    Returns:
        Query string with leading '?' or empty string if no params

    Examples:
        >>> build_query_string({"page": 1, "limit": 10})
        '?page=1&limit=10'

        >>> build_query_string({"name": None, "age": 25}, skip_none=True)
        '?age=25'

        >>> build_query_string({})
        ''
    """
    if not params:
        return ""

    # Filter out None and empty values if requested
    filtered = {}
    for key, value in params.items():
        if skip_none and value is None:
            continue
        if skip_empty and value == "":
            continue
        filtered[key] = value

    if not filtered:
        return ""

    return "?" + urlencode(filtered)


def build_path(*segments: str) -> str:
    """
    Build URL path from segments, handling slashes properly.

    Args:
        *segments: Path segments to join

    Returns:
        Joined path with proper slashes (leading slash, no trailing slash)

    Examples:
        >>> build_path("/api", "apps/", "/my-app/", "datatables")
        '/api/apps/my-app/datatables'

        >>> build_path("api", "users", "alice")
        '/api/users/alice'
    """
    # Strip leading/trailing slashes from each segment
    cleaned = [seg.strip('/') for seg in segments if seg]

    if not cleaned:
        return '/'

    # Join with single slash and ensure leading slash
    return '/' + '/'.join(cleaned)


def safe_get_nested(data: dict, *keys: str, default: Any = None) -> Any:
    """
    Safely get nested dictionary value without KeyError.

    Args:
        data: Dictionary to traverse
        *keys: Keys to access in order
        default: Default value if key not found (default: None)

    Returns:
        Value at nested key path, or default if not found

    Examples:
        >>> response = {"meta": {"access_token": "jwt_123"}}
        >>> safe_get_nested(response, "meta", "access_token")
        'jwt_123'

        >>> safe_get_nested(response, "data", "user", "email", default="unknown")
        'unknown'
    """
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key)
        else:
            return default

    return data if data is not None else default


def build_params(
    *,
    skip_none: bool = True,
    skip_empty: bool = True,
    **kwargs: Any
) -> dict[str, Any]:
    """
    Build parameter dictionary with optional filtering.

    Args:
        skip_none: Skip None values (default: True)
        skip_empty: Skip empty strings (default: True)
        **kwargs: Parameters to include

    Returns:
        Filtered parameter dictionary

    Examples:
        >>> build_params(page=1, limit=10, search=None)
        {'page': 1, 'limit': 10}

        >>> build_params(name="", age=25, skip_empty=True)
        {'age': 25}
    """
    params = {}

    for key, value in kwargs.items():
        if skip_none and value is None:
            continue
        if skip_empty and value == "":
            continue
        params[key] = value

    return params


__all__ = [
    "build_query_string",
    "build_path",
    "safe_get_nested",
    "build_params",
]
