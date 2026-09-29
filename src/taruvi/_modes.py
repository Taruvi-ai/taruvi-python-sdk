"""
Taruvi SDK runtime mode enum.

Kept in a dependency-free module so that ``taruvi.runtime`` and the package
``__init__`` can use ``RuntimeMode`` without importing ``taruvi.config`` (and
therefore ``pydantic_settings``) at import time. ``taruvi.config`` re-exports
it, so ``from taruvi.config import RuntimeMode`` keeps working.
"""

from enum import Enum


class RuntimeMode(str, Enum):
    """SDK runtime mode."""

    EXTERNAL = "external"  # Running in external application
    FUNCTION = "function"  # Running inside Taruvi function
    LOCAL_DEV = "local_dev"  # Local development/testing
