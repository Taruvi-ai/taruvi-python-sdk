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
    params: Optional[dict[str, Any]], *, skip_none: bool = True, skip_empty: bool = True
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
    cleaned = [seg.strip("/") for seg in segments if seg]

    if not cleaned:
        return "/"

    # Join with single slash and ensure leading slash
    return "/" + "/".join(cleaned)


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
    *, skip_none: bool = True, skip_empty: bool = True, **kwargs: Any
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


def combine_query_filters(
    flat: dict[str, Any] | None, raw: Any
) -> dict[str, Any] | list[Any] | None:
    """AND a flat filter dict with a complex filter object or a CrudFilters list.

    Either form alone is returned as itself. A list is turned into the same
    filter tree the platform builds, so a simple filter is not dropped when a
    Refine list is also set.
    """
    flat = dict(flat or {})
    if isinstance(raw, list):
        converted = _crud_list_to_tree(raw)
        raw = converted or (raw or None)
    elif not isinstance(raw, dict):
        raw = None
    if flat and raw:
        return {"and": [flat, raw]}
    if flat:
        return flat
    return raw or None


def _crud_list_to_tree(filters: list[Any]) -> dict[str, Any]:
    children = [child for child in (_crud_condition(item) for item in filters) if child]
    if not children:
        return {}
    if len(children) == 1:
        return children[0]
    return {"and": children}


def _crud_condition(item: Any) -> dict[str, Any]:
    if not isinstance(item, dict):
        return {}
    operator = item.get("operator", "eq")
    if operator in ("or", "and"):
        return {operator: [_crud_condition(child) for child in (item.get("value") or [])]}
    if operator == "not":
        inner = item.get("value")
        nested = _crud_condition(inner) if isinstance(inner, dict) else {}
        return {"not": nested} if nested else {}
    field = item.get("field") or ""
    if not field:
        return {}
    value = item.get("value", "")
    if operator in ("eq", None, ""):
        return {field: value}
    return {f"{field}__{operator}": value}


__all__ = [
    "build_params",
    "build_path",
    "build_query_string",
    "combine_query_filters",
    "safe_get_nested",
]
