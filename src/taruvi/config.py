"""
Taruvi SDK Configuration

Handles configuration from environment variables, .env files, and explicit parameters.
Supports both external application mode and function runtime mode.
"""

import os
from enum import Enum
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RuntimeMode(str, Enum):
    """SDK runtime mode."""

    EXTERNAL = "external"  # Running in external application
    FUNCTION = "function"  # Running inside Taruvi function
    LOCAL_DEV = "local_dev"  # Local development/testing


class TaruviConfig(BaseSettings):
    """
    Taruvi SDK configuration.

    Configuration precedence (highest to lowest):
    1. Explicit parameters passed to Client()
    2. Environment variables
    3. .env file (disabled in test mode)
    4. Default values
    """

    model_config = SettingsConfigDict(
        env_prefix="TARUVI_",
        env_file=".env" if os.getenv("TARUVI_TEST_MODE") != "true" else None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Core Configuration (Mandatory)
    api_url: str = Field(
        default="http://localhost:8000",
        description="Taruvi API base URL",
    )

    app_slug: str = Field(
        default="",
        description="Application slug (required)",
    )

    # Authentication Methods (All Optional)
    # Method 1: Knox API-Key
    api_key: Optional[str] = Field(
        default=None,
        description="Knox API key for authentication",
    )

    # Method 2: JWT Bearer Token
    jwt: Optional[str] = Field(
        default=None,
        description="JWT token (from any source: user-provided, login, or function runtime)",
    )

    # Method 3: Session Token
    session_token: Optional[str] = Field(
        default=None,
        description="Allauth session token",
    )

    # Method 4: Username+Password (for auto-login)
    username: Optional[str] = Field(
        default=None,
        description="Username for auto-login",
    )

    password: Optional[str] = Field(
        default=None,
        description="Password for auto-login",
    )

    # Legacy/Optional Configuration
    site_slug: Optional[str] = Field(
        default=None,
        description="Site slug for multi-tenant routing (optional)",
    )

    # Configuration
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds",
        ge=1,
        le=300,
    )

    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts",
        ge=0,
        le=10,
    )

    # Function Runtime Configuration (auto-detected)
    function_runtime: bool = Field(
        default=False,
        description="Whether running inside Taruvi function",
    )

    function_id: Optional[str] = Field(
        default=None,
        description="Function ID (when running inside function)",
    )

    function_name: Optional[str] = Field(
        default=None,
        description="Function name (when running inside function)",
    )

    execution_id: Optional[str] = Field(
        default=None,
        description="Execution ID (when running inside function)",
    )

    tenant: Optional[str] = Field(
        default=None,
        description="Tenant schema name (when running inside function)",
    )

    # User Context (for permission-aware operations)
    user_id: Optional[str] = Field(
        default=None,
        description="User ID for user-scoped operations",
    )

    user_email: Optional[str] = Field(
        default=None,
        description="User email",
    )

    user_jwt: Optional[str] = Field(
        default=None,
        description="User JWT token (for user context switching)",
    )

    def __init__(self, **kwargs):
        """Initialize configuration with runtime mode detection."""
        # Auto-detect function runtime mode
        if os.getenv("TARUVI_FUNCTION_RUNTIME") == "true":
            kwargs.setdefault("function_runtime", True)

        # In test mode, explicitly set auth fields to None if not provided
        # This prevents Pydantic from loading them from environment/.env file
        if os.getenv("TARUVI_TEST_MODE") == "true":
            kwargs.setdefault('api_key', None)
            kwargs.setdefault('jwt', None)
            kwargs.setdefault('session_token', None)
            kwargs.setdefault('username', None)
            kwargs.setdefault('password', None)

        super().__init__(**kwargs)

    @property
    def runtime_mode(self) -> RuntimeMode:
        """Detect current runtime mode."""
        if self.function_runtime:
            return RuntimeMode.FUNCTION

        if os.getenv("TARUVI_LOCAL_DEV") == "true":
            return RuntimeMode.LOCAL_DEV

        return RuntimeMode.EXTERNAL

    @property
    def headers(self) -> dict[str, str]:
        """Get default HTTP headers for API requests."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # AUTHENTICATION PRIORITY:
        # 1. Knox API-Key → Authorization: Api-Key {key}
        if self.api_key:
            headers["Authorization"] = f"Api-Key {self.api_key}"

        # 2. JWT (from any source) → Authorization: Bearer {jwt}
        elif self.jwt:
            headers["Authorization"] = f"Bearer {self.jwt}"

        # 3. Session token → X-Session-Token header (can combine with above)
        if self.session_token:
            headers["X-Session-Token"] = self.session_token

        # 4. No auth → Django session cookies (httpx automatic)

        # Add site slug for multi-tenant routing (if provided)
        if self.site_slug:
            headers["Host"] = f"{self.site_slug}.localhost"

        # Add execution context headers (for tracing)
        if self.execution_id:
            headers["X-Execution-ID"] = self.execution_id

        if self.function_id:
            headers["X-Function-ID"] = self.function_id

        return headers

    def validate_required_fields(self) -> None:
        """
        Validate that required fields are present.

        Raises:
            ConfigurationError: If required fields are missing
        """
        from taruvi.exceptions import ConfigurationError

        if not self.api_url:
            raise ConfigurationError("api_url is required")

        if not self.app_slug:
            raise ConfigurationError("app_slug is required")

        # All authentication is optional!

    def model_dump_safe(self) -> dict:
        """Dump configuration without sensitive data."""
        data = self.model_dump()
        # Redact sensitive fields
        if data.get("api_key"):
            data["api_key"] = "***REDACTED***"
        if data.get("jwt"):
            data["jwt"] = "***REDACTED***"
        if data.get("user_jwt"):
            data["user_jwt"] = "***REDACTED***"
        if data.get("password"):
            data["password"] = "***REDACTED***"
        if data.get("session_token"):
            data["session_token"] = "***REDACTED***"
        return data

    @classmethod
    def from_runtime_and_params(cls, **explicit_params) -> "TaruviConfig":
        """
        Create config from runtime environment and explicit parameters.

        Merges configuration from three sources (priority order):
        1. Explicit parameters (highest)
        2. Environment variables
        3. .env file (disabled in test mode)
        4. Default values (lowest)

        Pydantic automatically handles precedence.

        Args:
            **explicit_params: Explicitly provided parameters

        Returns:
            TaruviConfig: Merged configuration

        Example:
            ```python
            config = TaruviConfig.from_runtime_and_params(
                api_key="explicit_token",  # Overrides env vars
                site_slug=None  # Uses env var if available
            )
            ```
        """
        # Import here to avoid circular dependency
        from taruvi.runtime import detect_runtime, load_config_from_runtime

        runtime_mode = detect_runtime()

        # In test mode, explicitly set auth fields to None if not provided
        # This prevents Pydantic from loading them from environment/env file
        if os.getenv("TARUVI_TEST_MODE") == "true":
            test_defaults = {
                'api_key': None,
                'jwt': None,
                'session_token': None,
                'username': None,
                'password': None,
            }
            # Apply test defaults first, then override with explicit params
            explicit_params = {**test_defaults, **explicit_params}

        if runtime_mode == RuntimeMode.FUNCTION:
            # Load runtime config from environment
            runtime_config = load_config_from_runtime()

            # Merge: explicit params override runtime config
            # Filter None values from explicit params to allow runtime fallback
            filtered_params = {k: v for k, v in explicit_params.items() if v is not None}
            merged = {**runtime_config, **filtered_params}

            return cls(**merged)
        else:
            # EXTERNAL mode - use explicit params + env vars (Pydantic handles it)
            return cls(**explicit_params)
