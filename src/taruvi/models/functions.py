"""Functions API response models."""

from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class FunctionResponse(BaseModel):
    """Function details response."""

    id: str = Field(..., description="Function ID")
    name: str = Field(..., description="Function name")
    slug: str = Field(..., description="Function slug")
    execution_mode: str = Field(..., description="Execution mode (APP, DOCKER, etc.)")
    description: Optional[str] = Field(None, description="Function description")
    is_active: bool = Field(True, description="Is function active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    @classmethod
    def from_dict(cls, data: dict) -> "FunctionResponse":
        """Create from API response dict."""
        return cls.model_validate(data)


class FunctionExecutionResult(BaseModel):
    """Function execution result."""

    success: bool = Field(..., description="Execution success status")
    data: Any = Field(None, description="Execution result data")
    message: Optional[str] = Field(None, description="Execution message")
    stdout: Optional[str] = Field(None, description="Standard output")
    stderr: Optional[str] = Field(None, description="Standard error")

    # For async execution
    task_id: Optional[str] = Field(None, description="Task ID for async execution")
    status: Optional[str] = Field(None, description="Task status")

    @classmethod
    def from_dict(cls, data: dict) -> "FunctionExecutionResult":
        """Create from API response dict."""
        return cls.model_validate(data)


class InvocationResponse(BaseModel):
    """Function invocation details."""

    id: str = Field(..., description="Invocation ID")
    function_id: str = Field(..., description="Function ID")
    status: str = Field(..., description="Invocation status")
    result: Optional[Any] = Field(None, description="Invocation result")
    error: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="Creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")

    @classmethod
    def from_dict(cls, data: dict) -> "InvocationResponse":
        """Create from API response dict."""
        return cls.model_validate(data)


class FunctionListResponse(BaseModel):
    """List of functions with pagination."""

    data: list[FunctionResponse] = Field(..., description="Function list")
    total: int = Field(..., description="Total count")
    page: Optional[int] = Field(None, description="Current page")
    page_size: Optional[int] = Field(None, description="Page size")

    @classmethod
    def from_dict(cls, data: dict) -> "FunctionListResponse":
        """Create from API response dict."""
        # Convert nested dicts to FunctionResponse models
        functions = [FunctionResponse.from_dict(f) for f in data.get("data", [])]
        return cls(
            data=functions,
            total=data.get("total", len(functions)),
            page=data.get("page"),
            page_size=data.get("page_size")
        )
