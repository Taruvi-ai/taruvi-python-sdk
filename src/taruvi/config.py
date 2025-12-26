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
    3. .env file
    4. Default values
    """

    model_config = SettingsConfigDict(
        env_prefix="TARUVI_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Core Configuration
    api_url: str = Field(
        default="http://localhost:8000",
        description="Taruvi API base URL",
    )

    api_key: Optional[str] = Field(
        default=None,
        description="API key (JWT token) for authentication",
    )

    site_slug: Optional[str] = Field(
        default=None,
        description="Site slug for multi-tenant routing",
    )

    # Optional Configuration
    app_slug: Optional[str] = Field(
        default=None,
        description="App slug (for scoping operations)",
    )

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

    retry_backoff_factor: float = Field(
        default=0.5,
        description="Backoff factor for retries (exponential backoff)",
        ge=0.0,
    )

    # Connection Pool Settings
    pool_connections: int = Field(
        default=10,
        description="Number of connection pool connections",
        ge=1,
    )

    pool_maxsize: int = Field(
        default=10,
        description="Maximum size of connection pool",
        ge=1,
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

    # Development/Debug
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )

    verify_ssl: bool = Field(
        default=True,
        description="Verify SSL certificates",
    )

    def __init__(self, **kwargs):
        """Initialize configuration with runtime mode detection."""
        # Auto-detect function runtime mode
        if os.getenv("TARUVI_FUNCTION_RUNTIME") == "true":
            kwargs.setdefault("function_runtime", True)

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

        # Add API key (JWT token)
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # Add site slug for multi-tenant routing
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

        if not self.api_key and self.runtime_mode == RuntimeMode.EXTERNAL:
            raise ConfigurationError(
                "api_key is required for external applications. "
                "Provide it via Client(api_key=...) or TARUVI_API_KEY environment variable."
            )

        if not self.site_slug:
            raise ConfigurationError(
                "site_slug is required. "
                "Provide it via Client(site_slug=...) or TARUVI_SITE_SLUG environment variable."
            )

    def model_dump_safe(self) -> dict:
        """Dump configuration without sensitive data."""
        data = self.model_dump()
        # Redact sensitive fields
        if data.get("api_key"):
            data["api_key"] = "***REDACTED***"
        if data.get("user_jwt"):
            data["user_jwt"] = "***REDACTED***"
        return data
