"""
Runtime Detection and Context

Detects whether SDK is running inside a Taruvi function or in an external application.
Provides access to function execution context when available.
"""

import os
from typing import Any, Optional

from taruvi.config import RuntimeMode


def detect_runtime() -> RuntimeMode:
    """
    Detect current runtime environment.

    Returns:
        RuntimeMode: The detected runtime mode
    """
    # Check if running inside Taruvi function
    if os.getenv("TARUVI_FUNCTION_RUNTIME") == "true":
        return RuntimeMode.FUNCTION

    # Check if local development
    if os.getenv("TARUVI_LOCAL_DEV") == "true":
        return RuntimeMode.LOCAL_DEV

    # Default to external application
    return RuntimeMode.EXTERNAL


def is_inside_function() -> bool:
    """
    Check if SDK is running inside a Taruvi function.

    Returns:
        bool: True if inside function, False otherwise
    """
    return detect_runtime() == RuntimeMode.FUNCTION


def get_function_context() -> Optional[dict[str, Any]]:
    """
    Get function execution context when running inside a function.

    Returns:
        Optional[dict]: Function context if inside function, None otherwise

    Example:
        ```python
        context = get_function_context()
        if context:
            print(f"Running in function: {context['function_name']}")
            print(f"Execution ID: {context['execution_id']}")
        ```
    """
    if not is_inside_function():
        return None

    return {
        "function_id": os.getenv("TARUVI_FUNCTION_ID"),
        "function_name": os.getenv("TARUVI_FUNCTION_NAME"),
        "execution_id": os.getenv("TARUVI_EXECUTION_ID"),
        "tenant": os.getenv("TARUVI_TENANT"),
        "app_id": os.getenv("TARUVI_APP_ID"),
        "app_slug": os.getenv("TARUVI_APP_SLUG"),
        "site_id": os.getenv("TARUVI_SITE_ID"),
        "site_slug": os.getenv("TARUVI_SITE_SLUG"),
        "api_url": os.getenv("TARUVI_API_URL"),
        "function_key": os.getenv("TARUVI_FUNCTION_KEY"),
        "user_id": os.getenv("TARUVI_USER_ID"),
        "user_email": os.getenv("TARUVI_USER_EMAIL"),
    }


def get_execution_metadata() -> dict[str, Any]:
    """
    Get execution metadata for current runtime.

    Returns:
        dict: Execution metadata including mode and context

    Example:
        ```python
        metadata = get_execution_metadata()
        print(f"Mode: {metadata['mode']}")
        print(f"Function: {metadata.get('function_name', 'N/A')}")
        ```
    """
    mode = detect_runtime()
    metadata: dict[str, Any] = {
        "mode": mode.value,
        "is_function": mode == RuntimeMode.FUNCTION,
    }

    if mode == RuntimeMode.FUNCTION:
        context = get_function_context()
        if context:
            metadata.update(context)

    return metadata


def load_config_from_runtime() -> dict[str, Any]:
    """
    Load configuration from runtime environment.

    Used by SDK to auto-configure when running inside a function.

    Returns:
        dict: Configuration extracted from environment
    """
    if not is_inside_function():
        return {}

    context = get_function_context()
    if not context:
        return {}

    return {
        "api_url": context.get("api_url"),
        "jwt": context.get("function_key"),  # Load function JWT into jwt field
        "site_slug": context.get("site_slug"),
        "app_slug": context.get("app_slug"),
        "function_runtime": True,
        "function_id": context.get("function_id"),
        "function_name": context.get("function_name"),
        "execution_id": context.get("execution_id"),
        "tenant": context.get("tenant"),
        "user_id": context.get("user_id"),
        "user_email": context.get("user_email"),
    }
