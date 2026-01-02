"""App API response models."""

from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class Role(BaseModel):
    """App role response."""

    id: Optional[str | int] = Field(None, description="Role ID")
    name: Optional[str] = Field(None, description="Role name")
    permissions: Optional[list[str]] = Field(None, description="Role permissions")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        extra = "allow"  # Allow additional fields

    @classmethod
    def from_dict(cls, data: dict) -> "Role":
        """Create from API response dict."""
        return cls.model_validate(data)


class RoleListResponse(BaseModel):
    """List of roles."""

    data: list[Role] = Field(..., description="Roles list")
    total: int = Field(..., description="Total count")

    @classmethod
    def from_dict(cls, data: dict) -> "RoleListResponse":
        """Create from API response dict."""
        roles = [Role.from_dict(r) for r in data.get("data", [])]
        return cls(
            data=roles,
            total=data.get("total", len(roles))
        )


class UserApp(BaseModel):
    """User's app information."""

    name: str = Field(..., description="App name")
    slug: str = Field(..., description="App slug")
    icon: Optional[str] = Field(None, description="App icon URL")
    url: Optional[str] = Field(None, description="App URL")
    display_name: Optional[str] = Field(None, description="App display name")

    @classmethod
    def from_dict(cls, data: dict) -> "UserApp":
        """Create from API response dict."""
        return cls.model_validate(data)
